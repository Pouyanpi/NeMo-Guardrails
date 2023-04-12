from colangflows.actions import action


@action()
async def check_service_status():
    return "online"
