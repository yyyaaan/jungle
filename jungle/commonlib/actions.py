# logger is in secret manager
from .vmmanager import *

def perform_action(validated_request):
    # startup, shutdown based on vmid_list
    # logger.info("Action received from VM Action Serializer")
    results = ["-"]

    try:
        action = validated_request["event"]
        vmid_list = [x.vmid for x in validated_request["vmids"]]

        if action == "START":
            for vmid in vmid_list:
                status, info = vm_startup(vmid)
                results.append(info)            
        elif action == "STOP":
            for vmid in vmid_list:
                status, info = vm_shutdown(vmid)
                results.append(info)
        else:
            logger.warn(f"Unknown action {action}")
            results.append(f"Unkonw action")
    except Exception as e:
        logger.error(f"Error in performing action: {str(e)}")
        results.append(f"Error occured: {str(e)}")

    validated_request['result'] = "; ".join(results)
    return validated_request


