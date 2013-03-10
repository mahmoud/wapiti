Notes
=====

Notes on "multiargument" and "bijective":
-----------------------------------------

There are lots of ways to classify operations, and these are just a
couple.

"Multiargument" operations can take more than one search parameter
at once, such as the GetProtections operation. Others, can only take
one argument at a time, like GetCategory.

"Bijective" only return at most one result per argument. GetProtections
is an example of a bijective query. Bijective queries do not require an
explicit limit on the number of results to be set by the user.

Going forward, these attributes can be determined as follows:

- Multiargument: determined by looking at an operation's
  `input_field`. If it is a SingleParam, then multiargument is false,
  if it's a MultiParam, then multiargument is true.

- Bijective: determined by looking at an operation's `output_type`,
  which more accurately describes the *per-parameter* return type. If
  it is a list, then bijective is true, if it's a bare type, then
  bijective is false.


Fodder from DSL/dataflow refactor
---------------------------------

GetCategoryPagesRecursive
(FlattenCategory -> GetCategoryPages -> Wikipedia API call -> URL fetch     )
(PageInfos       <- PageInfos        <- MediaWikiCall      <- RansomResponse)

operation's input_field = explicit or first field of chain

def process(op):
   res = op.process()
   return self.store_results(res)

what about producing subops?

def process():
   task = self.get_current_task()
   res = task.process()
   if res and isinstance(res[0], Operation):
      self.store_subops(res)
      return  # return subops?
   return self.store_results(res)  # returns *new* results

GetCategoryPagesRecursive
(FlattenCategory --(CatInfos)->
        GetCategoryPages --("APIParamStructs")->
               MediawikiCall [--(url)-> URL fetch])

An "APIParamStruct" is really just something with the API url and param
dictionary, so QueryOperations themselves could be viewed as
APIParamStructs. In other words, hopefully no new model type needed
just for that.

At its most basic level, an Operation is something which:

- Has a type-declared input field, and a declared return type
- Has a process() function that returns results (of the output type)
  or raises NoMoreResults
- Most likely takes a WapitiClient as a 'client' keyword
  argument in its __init__()
- Provides a uniform way of checking progress (checking if it's done)

Some notes on Operation design/usage:

- An Operation typically keeps a copy of its results internally,
  most likely a unique list of some sort, and should return only
  new results.
- Calling an Operation directly calls process() repeatedly until the
  operation is complete, then returns the internally tracked results.
