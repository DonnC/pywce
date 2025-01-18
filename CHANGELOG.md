## [1.0.0] - Jan 2025.
* Initial release.


## [1.0.1] - Jan 2025.
* Support for `@hook` decorator on hooks
* Added new default session manager implementation using `cachetool` lib

Decorator enables hook caching

This enhance developer productivity and provides future support like hook metrics and performance
```python
from pywce import hook, HookArg, TemplateDynamicBody

@hook
def username(arg: HookArg) -> HookArg:
    """
    A template to get default user whatsapp username.

    :param arg: HookArg passed by engine
    :return: updated HookArg
    """
    arg.template_body = TemplateDynamicBody(
        render_template_payload={"name": arg.user.name}
    )

    return arg
```