---
title: {{ title }}
date: {{ datestr }}
{% if layout %}layout: {{ layout }}
{% endif %}{% if author %}author: "{{ author }}"
{% endif %}{% if categories %}categories: {% for category in categories %}{{ category }}{% if loop.last %}{% else %},{% endif %}{% endfor %}
{% endif %}version: {{ version }}
download: {{ download_url }}
---

Download from GitHub [here]({% raw %}{{ page.download }}{% endraw %})

# Release Notes

{{ notes }}
