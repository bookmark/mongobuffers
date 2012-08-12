Benefits

	- Forward/backwards compatible storage schema
	- Allows renaming of fields at any time
	- Keys are stored as integers represented as string. This yields smaller document objects.

Rules

	- One may add new unrequired fields at any time as long as the id number has not been used before.
	- One may rename fields at any time.
	- One may NOT change the ids for any existing fields.
	- Any new fields that added should be optional. 
	- Non-required fields can be removed, as long as the id is not used again.
	Recommended pratice is to rename the field, perhaps adding an "OBSOLETE_"
	prefix so future users can't reuse the number
	
An example Model with submodel::

    import datetime
    from mongobuffers.api import Model, Field
    
	class TestSubModel(Model):
        title = Field(1, type=str, required=False)
        text = Field(2, type=str, required=False)
        tags = Field(3, type=str, required=False, repeated=True)
        
    class TestModel(Model):
        title = Field(1, type=str, required=False)
        tags = Field(3, type=str, required=False, repeated=True)
        date = Field(4, type=datetime.datetime, required=False)
        videos = Field(5, type=str, required=False, repeated=True)
        text = Field(7, type=str, required=False)
        url = Field(9, type=str, required=False, info='''''')
        submodel = Field(10, type=TestSubModel, required=False)

Connecting a model to a database::
    
    db = pymongo.Connection().db
    
    TestModel = TestModel.connect(db)
    
Setting a value::
    
    n = TestModel()
    n.set('title', 'test')
    
Getting a value::
    
    n.get('title')

Saving a model::
    
    n.save()
    
Searching using mongo search specifications::
    
    # TestModel.spec is used to convert the search spec to use field ids
    spec = TestModel.spec({'title':'test'})
    
    # all the pymongo.Collection methods are available under TestModel.get_collection()
    TestModel.get_collection().find(spec, as_class=TestModel)
    
Removing a single model::
    
    n.remove()
