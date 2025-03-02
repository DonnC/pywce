from pywce import HookArg

## [1.0.0] - Jan 2025.

* Initial release.

## [1.0.1] - Jan 2025.

* Support for `@hook` decorator on hooks
* Added new default session manager implementation using `cachetool` lib

Decorator enables hook caching

This enhances developer productivity and provides future support like hook metrics and performance

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

## [1.0.2] - Feb 2025

* Added global config for toggling `read_receipts` property
* Added global config for toggling `tag_on_reply` property to enable disable reply to message
* CTA buttons now supported
```yaml
"GITHUB-PROFILE":
  type: cta
  message:
    title: "Support"
    body: "View my GitHub profile, contribute or support 🙈"
    url: "https://github.com/DonnC"
    button: "GitHub"
  routes:
    "re:.*": "START-MENU"
```

## [1.0.3] - Feb 2025
* Added basic live support portal
* added flag to pywce logger to toggle rotating file handler

## [1.0.4] - Feb 2025
* Simplify example projects
* Support for [catalog, single and multi product](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services/share-products) messages
```yaml
# catalog message
"VIEW-CATALOG-ITEM":
  type: catalog
  message:
    body: "Order on the go. Visit out catalog and add items to buy!"
    product-id: "your-thumbnail-product-retailer-id"
  routes:
    "re:.*": "VIEW-SINGLE-ITEM"

# single product message
"VIEW-SINGLE-ITEM":
  type: product
  message:
    body: "Check out our latest product on offer"
    catalog-id: "your-catalog-id"
    product-id: "your-thumbnail-product-retailer-id"
  routes:
    "re:.*": "VIEW-MULTI-ITEMS"

# many products message
"VIEW-MULTI-ITEMS":
  type: products
  message:
    title: Menu
    body: "Check out our latest menu"
    catalog-id: "your-catalog-id"
    button: Shop Now
    sections:
      "Pizza Toppings":     # <- title
        - "product-id-1"
        - "product-id-2"
      "Burgers":
        - "product-id-3"
        - "product-id-4"
  routes:
    "re:.*": "START-MENU"
```

## [1.0.5] - Feb 2025
* [WhatsApp template messages](https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates) now supported - `template` hook is required to set whatsapp template message

Note that `template` hook is required for template message types

It should return template list of components e.g.

```python
# dotted.path.to.template.hook.py
from pywce import hook, HookArg, EngineConstants, TemplateDynamicBody

@hook
def whatsapp_template_hook(arg: HookArg):
    # TODO: handle business logic

    # add your list of dict entries matching your template
    template_components = []

    arg.template_body = TemplateDynamicBody(render_template_payload={EngineConstants.WHATSAPP_TEMPLATE_KEY: template_components})

    return arg
```

```yaml
"WHATSAPP-TEMPLATE-MESSAGE":
  type: template
  template: "dotted.path.to.template.hook.whatsapp_template_hook"
  message:
    name: "<your-template-name>"
    language: "your-template-lang"    # default to en_US
  routes:
    "re:.*": "NEXT-ROUTE"
```

* Added support for dynamic message processing

Note that `template` hook is required for dynamic message types.

Dynamic template can render any supported pywce message type.

> [!NOTE]
> Hook should return a dict that matches any supported message, message attribute structure

```python
# dotted.path.to.template.hook.py
from pywce import hook, HookArg, TemplateTypeConstants, TemplateDynamicBody


@hook
def dynamic_message(arg: HookArg):
    # TODO: handle business logic

    # an example dynamic CTA button message
    cta_btn_message = dict(
        title="Developer Profile",
        body="Check out my updated github profile",
        url="https://github.com/DonnC",
        button="GitHub"
    )

    arg.template_body = TemplateDynamicBody(
        typ=TemplateTypeConstants.CTA,
        render_template_payload=cta_btn_message
    )

    return arg
```

```yaml
"DYNAMIC-MESSAGE":
  type: dynamic
  template: "dotted.path.to.template.hook.dynamic_message"
  message: "{{ body }}"
  routes:
    "re:.*": "NEXT-ROUTE"
```

## [1.0.6] Feb 2025
* Support download media files
* Fixed verifying webhook payload
* Added a helper fastapi decorator for secure payload verification
* Support download media uploaded via flows
```python
# you receive files in hook additional_data flow message

hook_files =  [{'id': '1571385113..', 'mime_type': 'image/jpeg', 'sha256': 'lV..', 'file_name': '5d70f3e...jpg'}]

# you can download files by passing to utility method
files = []
for file in hook_files:
    f = await whatsapp.util.download_flow_media(file)
    files.append(f)

print("downloaded files: ", files)
```
* Added initial support for custom AI agent
* Can now define global pre & post hooks