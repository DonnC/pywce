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
* [WhatsApp template messages](https://developers.facebook.com/docs/whatsapp/business-management-api/message-templates) now supported - `template` hook is required to set whatsapp template message

Note that `template` hook is required for template message types
```yaml
"WHATSAPP-TEMPLATE-MESSAGE":
  type: template
  template: "dotted.path.to.template.hook"
  message: "{{ body }}"
  routes:
    "re:.*": "NEXT-ROUTE"
```

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

