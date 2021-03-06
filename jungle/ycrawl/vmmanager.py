from json import dumps, loads
from logging import getLogger

from jungle.authentication import get_secret
from ycrawl.models import VmRegistry

SECRET = loads(get_secret("ycrawl-credentials"))


#####################################################
#    ___                       _             _    
#   / _ \ _ __   ___ _ __  ___| |_ __ _  ___| | __
#  | | | | '_ \ / _ \ '_ \/ __| __/ _` |/ __| |/ /
#  | |_| | |_) |  __/ | | \__ \ || (_| | (__|   < 
#   \___/| .__/ \___|_| |_|___/\__\__,_|\___|_|\_\
#        |_|                                         
# clouds.yaml includes crendentials #################


import openstack
# https://docs.openstack.org/openstacksdk/latest/user/proxies/compute.html
openstack.enable_logging(debug=False)
openstackconn = openstack.connect(cloud='openstack')

def csc_list_instances():
    vm_names = [x.vmid for x in VmRegistry.objects.filter(provider="CSC")]

    out_list, n_running = [], 0
    for instance in openstackconn.compute.servers():
        if str(instance.name) not in vm_names:
            logger.warn(f"CSC instance {instance.name} is not registered")
        out_list.append({
            "vmid": str(instance.name),
            "header": f"{instance.name} {instance.vm_state} (csc-nova)  {instance.flavor['original_name']}",
            "content": dumps(str(instance)).replace(", ", ",<br/>").replace('\\"', '"')[1:-1]
        })
        if instance.vm_state == 'active': 
            n_running += 1

    return n_running, out_list


def csc_vm_startup(vmid):
    the_vm = [x for x in openstackconn.compute.servers() if x.name == vmid].pop()
    vm_status = str(the_vm.vm_state)

    if vm_status == "active":
        return False, f"{vmid} is already active, no action"
    try:
        openstackconn.compute.unshelve_server(the_vm)
        return True, f"restarting {vmid} (was {vm_status})"
    except Exception as e:
        return False, f"starting {vmid} failed due to {str(e)}"


def csc_vm_shutdown(vmid):
    the_vm = [x for x in openstackconn.compute.servers() if x.name == vmid][0]

    if the_vm.vm_state != "active":
        return False, f"{vmid} is not running, no action."
    try:
        openstackconn.compute.shelve_server(the_vm)
        return True, f"shutting down {vmid}"
    except Exception as e:
        return False, f"shutting down {vmid} failed due to {str(e)}"



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

def gcp_list_instances():
    zones = [x.zone for x in VmRegistry.objects.filter(provider="GCP")]
    out_list, n_running = [], 0

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


def gcp_vm_startup(vmid, zone):
    vm_check = [x for x in GCE_CLIENT.list(project="yyyaaannn", zone=zone) if x.name == vmid]
    vm_status = [x.status for x in vm_check][0]
    vm_restricted = [x.start_restricted for x in vm_check][0]

    if vm_status == "RUNNING":
        return False, f"{vmid} is already active, no action"
    if vm_restricted:
        return False, f"{vmid}({vm_status}) is restricted."
    try:
        GCE_CLIENT.start_unary(project="yyyaaannn", zone=zone, instance=vmid)
        return True, f"restarting {vmid} (was {vm_status})"
    except Exception as e:
        return False, f"starting {vmid} failed due to {str(e)}"


def gcp_vm_shutdown(vmid, zone):
    vm_check = [x for x in GCE_CLIENT.list(project="yyyaaannn", zone=zone) if x.name == vmid]
    vm_status = [x.status for x in vm_check][0]

    if vm_status != "RUNNING":
        return False, f"{vmid} is not running, no action."
    try:
        GCE_CLIENT.stop_unary(project="yyyaaannn", zone=zone, instance=vmid)
        return True, f"shutting down {vmid}"
    except Exception as e:
        return False, f"shutting down {vmid} failed due to {str(e)}"



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


def azure_list_instances():
    resource_groups=[x.resource for x in VmRegistry.objects.filter(provider="Azure")]
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


def azure_vm_startup(vmid, resource_group):
    vm_status = ACE_CLIENT.virtual_machines.get(resource_group, vmid, expand='instanceView').instance_view.statuses[1].display_status

    if vm_status == "VM running":
        return False, f"{vmid} is already active, no action"
    try:
        ACE_CLIENT.virtual_machines.begin_start(resource_group, vmid)
        return True, f"restarting {vmid} (was {vm_status.upper().replace(' ', '')})"
    except Exception as e:
        return False, f"restart {vmid} failed due to {str(e)}"
    

def azure_vm_shutdown(vmid, resource_group):
    vm_status = ACE_CLIENT.virtual_machines.get(resource_group, vmid, expand='instanceView').instance_view.statuses[1].display_status
    # Azure: power off is billable, must be deallocated
    
    if vm_status != "VM running":
        return False, f"{vmid} is not running, no action"
    try: 
        ACE_CLIENT.virtual_machines.begin_deallocate(resource_group, vmid)
        return True, f"shutting down {vmid}"
    except Exception as e:
        logger.info(f"Completion noted: shutting down failed due to {str(e)}")
        return False, f"shutting down {vmid} failed due to {str(e)}"


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
    the_vm = VmRegistry.objects.filter(resource=instance_id).first()

    return boto3.client(
        "ec2",
        region_name = the_vm.zone[:-1],
        aws_access_key_id=SECRET['AWS_ACCESS_KEY'],
        aws_secret_access_key=SECRET['AWS_SECRET']
    )


def aws_list_instances():
    instance_ids = [x.resource for x in VmRegistry.objects.filter(provider="AWS")]
    out_list, n_running = [], 0

    try:
        instance_list = [aws_get_client(one_id).describe_instances(InstanceIds=[one_id]) for one_id in instance_ids]
        print("ok")
        for instance_info in instance_list:
            instance = instance_info['Reservations'][0]['Instances'][0]
            out_list.append({
                "vmid": str(instance['Tags'][0]['Value']),
                "header": f"{instance['Tags'][0]['Value']} {instance['State']['Name'].upper()} ({instance['Placement']['AvailabilityZone']}) {instance['InstanceType']}",
                "content": dumps(str(instance)).replace(", '", ",<br/>'")[2:-2]
            })
            if instance['State']['Name'] == 'running':
                n_running +=1
    except Exception as e:
        logger.error(str(e))

    return n_running, out_list


def aws_vm_startup(vmid, instance_id):

    ec2_client = aws_get_client(instance_id)
    vm_status = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['State']['Name'].upper()

    if vm_status == "RUNNING":
        return False, f"{vmid} is already active, no action"
    try:
        ec2_client.start_instances(InstanceIds=[instance_id])
        return True, f"restarting {vmid} (was {vm_status.upper().replace(' ', '')})"
    except Exception as e:
        return False, f"starting {vmid} failed due to {str(e)}"


def aws_vm_shutdown(vmid, instance_id):
    ec2_client = aws_get_client(instance_id)
    vm_status = ec2_client.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]['State']['Name'].upper()

    if vm_status != "RUNNING":
        return False, f"{vmid} is not running, no action"
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
        return True, f"shutting down {vmid}"
    except Exception as e:
        return False, f"shutting down failed due to {str(e)}"


#########################################################
#   __  __       _ _   _        ____ _                 _ 
#  |  \/  |_   _| | |_(_)      / ___| | ___  _   _  __| |
#  | |\/| | | | | | __| |_____| |   | |/ _ \| | | |/ _` |
#  | |  | | |_| | | |_| |_____| |___| | (_) | |_| | (_| |
#  |_|  |_|\__,_|_|\__|_|      \____|_|\___/ \__,_|\__,_|
#########################################################

def vm_list_all():
    n1, vms1 = gcp_list_instances()
    n2, vms2 = azure_list_instances()
    n3, vms3 = aws_list_instances()
    n4, vms4 = csc_list_instances()

    n_running, vm_list = n1+n2+n3+n4, vms1+vms2+vms3+vms4

    vm_list.sort(key=lambda x: x["header"])
    for i, x in enumerate(vm_list):
        x["icon"] = f"filter_{i+1}"

    return n_running, vm_list


def vm_startup(vmid):
    if str(vmid)[:4] == "test":
        return True, f"start {vmid} passed"

    the_vm = VmRegistry.objects.filter(vmid=vmid).first()

    if not the_vm:
        return False, "VM not registered"
    if the_vm.provider == "GCP":
        return gcp_vm_startup(vmid=the_vm.vmid, zone=the_vm.zone)
    if the_vm.provider == "Azure":
        return azure_vm_startup(vmid=the_vm.vmid, resource_group=the_vm.resource)
    if the_vm.provider == "AWS":
        return aws_vm_startup(vmid=the_vm.vmid, instance_id=the_vm.resource)
    if the_vm.provider == "CSC":
        return csc_vm_startup(vmid=the_vm.vmid)



def vm_shutdown(vmid):
    if str(vmid)[:4] == "test":
        return True, f"stop {vmid} passed"

    the_vm = VmRegistry.objects.filter(vmid=vmid).first()

    if not the_vm:
        return False, "VM not registered"
    if the_vm.provider == "GCP":
        return gcp_vm_shutdown(vmid=the_vm.vmid, zone=the_vm.zone)
    if the_vm.provider == "Azure":
        return azure_vm_shutdown(vmid=the_vm.vmid, resource_group=the_vm.resource)
    if the_vm.provider == "AWS":
        return aws_vm_shutdown(vmid=the_vm.vmid, instance_id=the_vm.resource)
    if the_vm.provider == "CSC":
        return csc_vm_shutdown(vmid=the_vm.vmid)
