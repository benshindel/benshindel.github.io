---
layout: cookbook
title: Cookbook
permalink: /cookbook/
noindex: true
sitemap: false
---

<ul class="recipe-list">
  {% for recipe in site.recipes %}
  <li><a href="{{ recipe.url | relative_url }}">{{ recipe.title }}</a></li>
  {% endfor %}
</ul>
