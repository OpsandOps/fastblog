## For the love of Django, I created a shell with Ipython where i can test out the Sqlalchemy ORM and just get a feel good from the native django shell

1:  start shell: ```python shell.py```

2: in shell, do the following
### 1. Test Pydantic Validation (like Django forms)
>>> user_data = UserCreate(username="john", email="bad_email") 
# (This will throw a validation error because email is invalid)

>>> valid_data = UserCreate(username="john", email="john@test.com")

# 2. Test the ORM Create pattern
>>> new_user = User(username=valid_data.username, email=valid_data.email)
>>> db.add(new_user)
>>> db.commit()
>>> db.refresh(new_user)

# 3. Test the ORM Read pattern
*creates a result.ChunkedIteratorResult in memory, retuens a list, in Django a Queryset*
>>> result = db.execute(select(User).where(User.username == "john"))
*returns the model object as a list, in django a dictionary of the first row that matches the where SQL filter username == "john" *
>>> my_user = result.scalars().first()
*[optional] convert to dictionary the fastapi way*
>>># Convert it to a dictionary using your Pydantic schema!
user_dict = UserResponse.model_validate(my_user).model_dump()
>>># or simply use the __dict__() method on my_user
>>> my_user.username
'john'
>>> my_user.__dict__

# 4. Test the Relationship
>>> new_post = Post(title="Hello", content="World", user_id=my_user.id)
>>> db.add(new_post)
>>> db.commit()

>>> my_user.posts
[<models.Post object at 0x...>]
>>> my_user.posts[0].author.username
'john'

>>> exit()