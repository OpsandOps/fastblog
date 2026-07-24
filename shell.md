## For the love of Django, I created a shell with Ipython where i can test out the Sqlalchemy ORM and just get a feel good from the native django shell

1:  start shell: ```python shell.py```

2: in shell, do the following
### 1. Test Pydantic Validation (like Django forms)
```bash
user_data = UserCreate(username="john", email="bad_email")
``` 
*This will throw a validation error because email is invalid*

```bash 
valid_data = UserCreate(username="john", email="john@test.com")
```

# 2. Test the ORM Create pattern
```bash
>>> new_user = User(username=valid_data.username, email=valid_data.email)
>>> db.add(new_user)
>>> db.commit()
>>> db.refresh(new_user)
```

# 3. Test the ORM Read pattern
*creates a result.ChunkedIteratorResult in memory, retuens a list, in Django a Queryset*
```bash
>>> result = db.execute(select(User).where(User.username == "john"))
```
*returns the model object as a list, in django a dictionary of the first row that matches the where SQL filter username == "john"*
```bash
my_user = result.scalars().first()
*[optional] convert to dictionary the fastapi way*
>>>  Convert it to a dictionary using your Pydantic schema!
>>> user_dict = UserResponse.model_validate(my_user).model_dump()
>>>  or simply use the __dict__() method on my_user
  my_user.username
'john'
>>> my_user.__dict__
```

## We manually pass user_id here. Later, this comes from the logged-in session
```bash
>>> new_post = Post(title="Hello FastAPI", content="SQLAlchemy is tricky but powerful", user_id=my_user.id)
>>> db.add(new_post)
>>> db.commit()
>>> db.refresh(new_post)

# Let's create a second post just to test lists later
>>> post_two = Post(title="Second Post", content="More content", user_id=my_user.id)
>>> db.add(post_two)
>>> db.commit()

# 4. Test the Relationship
# Grab our user again (or just use my_user from earlier)
>>> my_user = db.execute(select(User).where(User.username == "john")).scalars().first()

# This triggers a LAZY LOAD. SQLAlchemy will automatically write and execute a 
# "SELECT * FROM posts WHERE user_id = 1" query behind the scenes.
>>> my_user.posts
[<models.Post object at 0x...>, <models.Post object at 0x...>]

# Iterate through them just like a Django QuerySet
>>> for post in my_user.posts:
...     print(post.title)
... 
Hello FastAPI
Second Post

# Check the length (like Django's .count())
>>> len(my_user.posts)

>>> new_post = Post(title="Hello", content="World", user_id=my_user.id)
>>> db.add(new_post)
>>> db.commit()

## forward relationships
# Grab a post directly
>>> my_post = db.execute(select(Post).where(Post.title == "Hello FastAPI")).scalars().first()

# Access the single related User object
>>> my_post.author
<models.User object at 0x...>

# Chain attributes to get exactly what you want
>>> my_post.author.username
'john'
>>> my_post.author.email
'john@test.com'

>>> my_user.posts
[<models.Post object at 0x...>]
>>> my_user.posts[0].author.username
'john'

## nested relationships
>>> my_post = db.execute(select(Post).where(Post.title == "Hello FastAPI")).scalars().first()

# Validate the Post object (which contains a nested User object)
>>> post_dict = PostResponse.model_validate(my_post).model_dump()

>>> import pprint
>>> pprint.pprint(post_dict)
{'author': {'email': 'john@test.com',
            'id': 1,
            'image_file': None,
            'image_path': 'static/profile_pics/default.jpg',
            'username': 'john'},
 'content': 'SQLAlchemy is tricky but powerful',
 'created_at': datetime.datetime(2023, 10, 27, 15, 30, 0, tzinfo=datetime.timezone.utc),
 'id': 1,
 'title': 'Hello FastAPI',
 'updated_at': None,
 'user_id': 1}

## advanced filtering using .join() 
# We use .join() to link the tables, then apply the .where() on the User table
>>> stmt = select(Post).join(User).where(User.username == "john")

# Execute and get all matching posts
>>> johns_posts = db.execute(stmt).scalars().all()

>>> for p in johns_posts:
...     print(f"Post: {p.title} | By: {p.author.username}")
...
Post: Hello FastAPI | By: john
Post: Second Post | By: john
```
*exit shell*
``` exit() ```