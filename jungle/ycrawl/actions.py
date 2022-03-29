from .models import logger

def perform_action(validated_request):
    # startup, shutdown based on vmid_list
    # logger.info("Action received from VM Action Serializer")
    action = validated_request["event"]
    vmid_list = [x.vmid for x in validated_request["vmids"]]

    if action == "START":
        for vmid in vmid_list:
            logger.info(f"Action initiated: start {vmid}")
        return True 

    if action == "STOP":
        for vmid in vmid_list:
            logger.info(f"Action initiated: stop {vmid}")
        return True

    logger.warn(f"Unknown action")
    return False


