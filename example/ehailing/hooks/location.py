from pywce import hook, HookArg
@hook
def save_destination(arg: HookArg) -> HookArg:
    print(f"Destination hook arg: {arg}")

    # TODO: assess arg and implement business logic
    #       Data will be available in the arg.additional_data

    return arg
