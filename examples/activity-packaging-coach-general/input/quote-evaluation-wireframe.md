# Supplier quote evaluation wireframe

<!--WFDATA
{"id":"PROC-4-2-1","owner":"sourcing-analyst","lv4":"Strategic sourcing","lv5":"Supplier quote evaluation","lv6":"Quote normalization","skill":"quote-intake-normalizer","N":[{"no":1,"n":"Read quote bundle","col":1,"band":"main","e":"hm","sug":"rd","gate":0,"rule":"Read every fictional quote row","exc":"Missing files stop the run"},{"no":2,"n":"Normalize quote fields","col":2,"band":"main","e":"hm","sug":"cdx","gate":0,"rule":"Convert supported currency and preserve source evidence","exc":"Failed parse becomes review"}],"E":[{"a":0,"b":1,"dot":0}]}
-->

<!--WFDATA
{"id":"PROC-4-2-2","owner":"sourcing-analyst","lv4":"Strategic sourcing","lv5":"Supplier quote evaluation","lv6":"Variance analysis","skill":"quote-variance-analyzer","N":[{"no":1,"n":"Join normalized quotes and policy","col":1,"band":"main","e":"hm","sug":"rd","gate":0,"rule":"Match by item code","exc":"Missing match becomes review"},{"no":2,"n":"Apply variance rules","col":2,"band":"main","e":"hm","sug":"cdx","gate":1,"rule":"Price above 12% or lead time above 7 days requires review","exc":"Ambiguity routes to buyer"}],"E":[{"a":0,"b":1,"dot":0}]}
-->

<!--WFDATA
{"id":"PROC-4-2-3","owner":"buyer","lv4":"Strategic sourcing","lv5":"Supplier quote evaluation","lv6":"Buyer review brief","skill":"sourcing-review-brief","N":[{"no":1,"n":"Draft review brief","col":1,"band":"main","e":"hm","sug":"cdx","gate":0,"rule":"Summarize every quote and evidence","exc":"Missing evidence remains unresolved"},{"no":2,"n":"Buyer confirmation","col":2,"band":"main","e":"hm","sug":"hm","gate":1,"rule":"Buyer confirms exceptions and supplier choice","exc":"No purchase order is sent"}],"E":[{"a":0,"b":1,"dot":0}]}
-->
