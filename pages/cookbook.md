---
layout: cookbook
title: Cookbook
permalink: /cookbook/
---

<div class="cookbook-grid">
  {% for recipe in site.recipes %}
  <a href="{{ recipe.url | relative_url }}" class="cookbook-item">
    <div class="cookbook-item-icon">
      <img src="{{ '/assets/images/cookbook/' | append: recipe.svg_icon | relative_url }}" alt="{{ recipe.title }}">
    </div>
    <span class="cookbook-item-title">{{ recipe.title }}</span>
  </a>
  {% endfor %}
</div>
