{#
    Test générique : bornes inclusives sur une colonne (spec Phase 4 §5 « ranges »).

    Utilisation (un seul côté possible, les deux recommandés) :

        - name: bedrooms
          tests:
            - within_range:
                arguments:
                  min_value: 0
                  max_value: 10

    Le test échoue s'il remonte des lignes hors bornes. Les valeurs NULL ne sont
    pas signalées ici : leur contrôle relève de `not_null` (une colonne nullable
    — par exemple `median_rent_price`, non publiée sous le seuil — reste valide).
#}

{% test within_range(model, column_name, min_value=none, max_value=none) %}

{% if min_value is none and max_value is none %}
    {{ exceptions.raise_compiler_error(
        "within_range exige au moins `min_value` ou `max_value` (colonne '" ~ column_name ~ "')."
    ) }}
{% endif %}

select *
from {{ model }}
where
{% if min_value is not none %}
    {{ column_name }} < {{ min_value }}
{% endif %}
{% if min_value is not none and max_value is not none %}
    or
{% endif %}
{% if max_value is not none %}
    {{ column_name }} > {{ max_value }}
{% endif %}

{% endtest %}
