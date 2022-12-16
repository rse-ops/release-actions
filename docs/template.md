---
title: {{ title }}
date: {{ datestr }}
{% if layout %}layout: {{ layout }}
{% endif %}{% if author %}author: "{{ author }}"
{% endif %}{% if categories %}categories: {% for category in categories %}{{ category }}{% if forloop.last %}{% else %},{% endif %}{% endfor %}
{% endif %}version: {{ version }}
download: {{ download_url }}
---

Download from GitHub [here]({% raw %}{{ page.download }}{% endraw %})

{% if header %}{{ header }}{% endif %}

{{ notes }}
