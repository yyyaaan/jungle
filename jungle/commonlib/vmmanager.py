from json import dumps, loads

from .secretmanager import *
from ycrawl.models import VmRegistry

# changes from Flask project: print -> logger, all_vms from model format changed

all_vms = VmRegistry.objects.all()
GCP_VMLIST= dict([(x.vmid, x.zone) for x in all_vms if x.provider == "GCP"])
AZURE_VMLIST = dict([(x.vmid, x.resource) for x in all_vms if x.provider == "Azure"])
AWS_VMLIST = dict([(x.vmid, x.resource) for x in all_vms if x.provider == "AWS"])
SECRET = loads(get_secret("ycrawl-credentials"))


###############################################################
#    ____                   _         ____ _                 _ 
#   / ___| ___   ___   __ _| | ___   / ___| | ___  _   _  __| |
#  | |  _ / _ \ / _ \ / _` | |/ _ \ | |   | |/ _ \| | | |/ _` |
#  | |_| | (_) | (_) | (_| | |  __/ | |___| | (_) | |_| | (_| |
#   \____|\___/ \___/ \__, |_|\___|  \____|_|\___/ \__,_|\__,_|
#                     |___/                                    
# Auth using service account ##################################

from google.cloud import compute_v1
GCE_CLIENT = compute_v1.InstancesClient()

def gcp_list_instances(zones=["europe-north1-c"]):

    out_list, n_running = [], 0
    # zones = zones + ["europe-north1-c", "us-east1-b"] # can contain duplicates

    for zone in set(zones):
        instance_list = GCE_CLIENT.list(project="yyyaaannn", zone=zone)
        for instance in instance_list:
            restriced = "(Restricted Restart) " if instance.start_restricted else ""
            out_list.append({
                "vmid": str(instance.name),
                "header": f"{instance.name} {instance.status} {restriced} ({instance.zone.split('/')[-1]})  {instance.machine_type.split('/')[-1]}",
                "content": dumps(str(instance)).replace("\\n", "<br/>").replace('\\"', '"')[1:-1]
            })
            if instance.status == 'RUNNING':
                n_running += 1

    return n_running, out_list


def gcp_vm_startup(vmid, zone, keepinfo=False):
    vm_check = [x for x in GCE_CLIENT.list(project="yyyaaannn", zone=zone) if x.name == vmid]
    vm_status = [x.status for x in vm_check][0]
    vm_restricted = [x.start_restricted for x in vm_check][0]
    info = ""

    if vm_status != "RUNNING":
        if vm_restricted:
            logger.info(f"VM Manager: {vmid}({vm_status}) is restricted. Try next time.")
            return False

        info = f"VM Manager: restarting {vmid} (was {vm_status})"
        try:
            GCE_CLIENT.start_unary(project="yyyaaannn", zone=zone, instance=vmid)
        except Exception as e:
            logger.info(f"VM Manager: restart failed due to {str(e)}")
            return False

    if not keepinfo: logger.info(info)
    return True, info


def gcp_vm_shutdown(vmid, zone):
    vm_check = [x for x in GCE_CLIENT.list(project="yyyaaannn", zone=zone) if x.name == vmid]
    vm_status = [x.status for x in vm_check][0]

    if vm_status == "RUNNING":
        logger.info(f"Completion noted: shutting down {vmid}")
        try:
            GCE_CLIENT.stop_unary(project="yyyaaannn", zone=zone, instance=vmid)
        except Exception as e:
            logger.info(f"Completion noted: shutting down failed due to {str(e)}")
            return False
    else:
        logger.info(f"{vmid} is not running.")

    return True


############################################################################
#      _                          __  __ _                           __ _   
#     / \    _____   _ _ __ ___  |  \/  (_) ___ _ __ ___  ___  ___  / _| |_ 
#    / _ \  |_  / | | | '__/ _ \ | |\/| | |/ __| '__/ _ \/ __|/ _ \| |_| __|
#   / ___ \  / /| |_| | | |  __/ | |  | | | (__| | | (_) \__ \ (_) |  _| |_ 
#  /_/   \_\/___|\__,_|_|  \___| |_|  |_|_|\___|_|  \___/|___/\___/|_|  \__|
# Service principle (app registerations) ####################################


from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient

ACE_CLIENT = ComputeManagementClient(
    ClientSecretCredential(
        tenant_id=SECRET['AZURE_TENANT_ID'],
        client_id=SECRET['AZURE_CLIENT_ID'],
        client_secret=SECRET['AZURE_CLIENT_SECRET'],
    ),
    SECRET['AZURE_SUBSCRIPTION_ID']
)


def azure_list_instances(resource_groups=["VM-Workers"]):
    out_list, n_running = [], 0

    for group in set(resource_groups):
        instance_list = ACE_CLIENT.virtual_machines.list(group)
        for instance in instance_list:

            vm_status = ACE_CLIENT.virtual_machines.get(group, instance.name, expand='instanceView').instance_view.statuses[1].display_status
            out_list.append({
                "vmid": str(instance.name),
                "header": f"{instance.name} {vm_status.upper().replace(' ', '')} ({instance.location}) {instance.hardware_profile.vm_size}",
                "content": dumps(str(instance)).replace(", '", ",<br/>'")[2:-2]
            })
            if vm_status == 'VM running':
                n_running +=1

    return n_running, out_list


def azure_vm_startup(vmid, resource_group, keepinfo=False):
    vm_status = ACE_CLIENT.virtual_machines.get(resource_group, vmid, expand='instanceView').instance_view.statuses[1].display_status
    info = ""
    if vm_status != "VM running":
        info = f"VM Manager: restarting {vmid} (was {vm_status.upper().replace(' ', '')})"
        try:
            ACE_CLIENT.virtual_machines.begin_start(resource_group, vmid)
        except Exception as e:
            logger.info(f"VM Manager: restart failed due to {str(e)}")
            return False
    
    if not keepinfo: logger.info(info)
    return True, info


def azure_vm_shutdown(vmid, resource_group):
    logger.info(f"Completion noted: shutting down {vmid}")
    try:
        # Azure: power off is billable, must be deallocated
        ACE_CLIENT.virtual_machines.begin_deallocate(resource_group, vmid)
    except Exception as e:
        logger.info(f"Completion noted: shutting down failed due to {str(e)}")
        return False

    return True


####################################################################
#      ___        ______       _                                   
#     / \ \      / / ___|     / \   _ __ ___   __ _ _______  _ __  
#    / _ \ \ /\ / /\___ \    / _ \ | '_ ` _ \ / _` |_  / _ \| '_ \ 
#   / ___ \ V  V /  ___) |  / ___ \| | | | | | (_| |/ / (_) | | | |
#  /_/   \_\_/\_/  |____/  /_/   \_\_| |_| |_|\__,_/___\___/|_| |_|
# IAM User/Role Pair ###############################################
################################ AWS need region-sepcific client ###                                                                                                 
import boto3

def aws_get_client(instance_id):
    # client is region-binded, so need to determine proper cliente
    aws_regions = dict([(x.resource, x.zone[:-1]) for x in all_vms if x.provider == "AWS"])

    return boto3.client(
        "ec2",
        region_name = aws_regions[instance_id],
        aws_access_key_id=SECRET['AWS_ACCESS_KEY'],
        aws_secret_access_key=SECRET['AWS_SECRET']
    )


def aws_list_instances(instance_ids=["i-05baaec0fe7fe4d66", "i-07a9cb47522f26bf8"]):

    out_list, n_running = [], 0

    instance_list = [aws_get_client(one_id).describe_instances(InstanceIds=[one_id]) for one_id in instance_ids]
    
    for instance_info in instance_list:
        instance = instance_info['Reservations'][0]['Instances'][0]
        out_list.append({
            "vmid": str(instance['Tags'][0]['Value']),
            "header": f"{instance['Tags'][0]['Value']} {instance['State']['Name'].upper()} ({instance['Placement']['AvailabilityZone']}) {instance['InstanceType']}",
            "content": dumps(str(instance)).replace(", '", ",<br/>'")[2:-2]
        })
        if instance['State']['Name'] == 'running':
            n_running +=1

    return n_running, out_list


def aws_vm_startup(vmid, instance_id, keepinfo=False):

    ec2_client = aws_get_client(instance_id)
    info = ""
    
    vm_status = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['State']['Name'].upper()
    if vm_status != "RUNNING":
        info = f"VM Manager: restarting {vmid} (was {vm_status.upper().replace(' ', '')})"
        try:
           ec2_client.start_instances(InstanceIds=[instance_id])        
        except Exception as e:
            logger.info(f"VM Manager: restart failed due to {str(e)}")
            return False

    if not keepinfo: logger.info(info)
    return True, info


def aws_vm_shutdown(vmid, instance_id):
    logger.info(f"Completion noted: shutting down {vmid}")
    try:
        aws_get_client(instance_id).stop_instances(InstanceIds=[instance_id])
    except Exception as e:
        logger.info(f"Completion noted: shutting down failed due to {str(e)}")
        return False

    return True


#########################################################
#   __  __       _ _   _        ____ _                 _ 
#  |  \/  |_   _| | |_(_)      / ___| | ___  _   _  __| |
#  | |\/| | | | | | __| |_____| |   | |/ _ \| | | |/ _` |
#  | |  | | |_| | | |_| |_____| |___| | (_) | |_| | (_| |
#  |_|  |_|\__,_|_|\__|_|      \____|_|\___/ \__,_|\__,_|
#########################################################

def vm_list_all():
    n_running1, vm_list1 = gcp_list_instances(list(GCP_VMLIST.values()))
    n_running2, vm_list2 = azure_list_instances(list(AZURE_VMLIST.values()))
    n_running3, vm_list3 = aws_list_instances(list(AWS_VMLIST.values()))
    
    vm_list = vm_list1 + vm_list2 + vm_list3
    vm_list.sort(key=lambda x: x["header"])
    for i, x in enumerate(vm_list):
        x["icon"] = f"filter_{i+1}"

    return n_running1 + n_running2 + n_running3, vm_list


def vm_startup(vmid, keepinfo=False):
    status, info = False, ""
    if vmid in GCP_VMLIST.keys():
        status, info = gcp_vm_startup(vmid=vmid, zone=GCP_VMLIST[vmid], keepinfo=keepinfo)
    if vmid in AZURE_VMLIST.keys():
        status, info = azure_vm_startup(vmid=vmid, resource_group=AZURE_VMLIST[vmid], keepinfo=keepinfo)
    if vmid in AWS_VMLIST.keys():
        status, info = aws_vm_startup(vmid=vmid, instance_id=AWS_VMLIST[vmid], keepinfo=keepinfo)

    return status, info


def vm_shutdown(vmid):
    status = False
    if vmid in GCP_VMLIST.keys():
        status = gcp_vm_shutdown(vmid=vmid, zone=GCP_VMLIST[vmid])
    if vmid in AZURE_VMLIST.keys():
        status = azure_vm_shutdown(vmid=vmid, resource_group=AZURE_VMLIST[vmid])
    if vmid in AWS_VMLIST.keys():
        status = aws_vm_shutdown(vmid=vmid, instance_id=AWS_VMLIST[vmid])

    return status