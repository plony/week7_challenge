
{{ config(materialized='table') }}

SELECT *
FROM public.sales_data
