# thmbnl

## Installation steps

1. Pull source code:

```
git clone git@github.com:crogi93/thmbnl.git
```

2. Deploy with command

```
docker-compose up --build
```

3. Createsuperuser.

```
docker-compose exec web python3 manage.py createsuperuser
```

## TIERS

### 1.Basic

 - Can create thumbnails with 200px height

### 2. Premium

 - Can create thumbnails with 200 and 400px height
 - Can create/storage original image size

### 3. Enterpise

 - Can create thumbnails with 200 and 400px height
 - Can create/storage original image size
 - Can set expire time

## Request examples (CURL)

### GET:

```
curl -u user:password localhost:8000/api/thumbnails
```

### POST:

```
curl -u user:password -F file=file_path -F expire_after=seconds localhost:8000/api/thumbnails
```

`expire_after` need to be defined between 300 and 30000 in seconds

