# Wagtail xmlimport

An extension for importing model data form a n xml file into a Wagail project.

It's intended that the data can be used to create page models, image models, document models and more.

Currently available models:

    Page

`Inital work is to import form a Wordpress xml export but it's hoped it will be able to use it for other xml data sources.`

## Installation

* Install the package with `pip install wagtail-xmlimport` (not yet available) but can be installed with pip install -e wagtail-xmlimport for development.

* Add `wagtail_xmlimport` to INSTALLED_APPS in your project

# Inital setup

```
It's a good idead to include this and other folders listed below in your .gitignore to avoid exposing potentially private data to the world.
```

Place your xml files inside a folder `xml` at the root of your project. You can name them whatever you want as the file name is entered when later commands are run.

Add a `json` folder to the root of your project. There's a optional `discovery` command that will need to write to that folder. Again add the folder to your `.gitignore` file

## XML -> Wagtail model mapping

* The general process to import an xml file is
    
    1. Create a mapping file using the `discovery` command with the xml file to use
    2. Adjust the resulting json file to you needs (see blow)
    3. Run the import command on the same xml file

`The import command needs the json mapping file to exist to know which fields to include in the import` Those fields will be part of your Wagtail model.

# Mapping

A simple mapping file could be: (It always needs the root item.) This is the final mapping file format. See below how to get there using the discovery command but you could write the file from scratch.

```
{
  "root": {
    "file": ["books.xml"],
    "tag" : ["book"],
    "model": ["BookPage"]
  },
  "book: [],
  "author": ["author", "required"],
  "title": ["title", "required"],
  "genre": [],
  "price": [],
  "publish_date": ["published_on", "date"],
  "description": []
}
```
The `"required"` list item at the last position is used to set the field as required during the import. If any required field is empty that record won't be imported. 

The `"date"` list item is a future feature to validate & format a nice date for import, coming soon.

In the root item:

* `"file"` is the name of the xml to load
* `"tag"` is the tag name that is the parent tag of all the data tags you want to include in the import. e.g. `books.xml`
* `"model"` is the model the data will be imported to (Wagtail model name)

### Using the discover command

You can import a file as below...

```
<?xml version="1.0"?>
<catalog>
   <book id="bk101">
      <author>Gambardella, Matthew</author>
      <title>XML Developer's Guide</title>
      <genre>Computer</genre>
      <price>44.95</price>
      <publish_date>2000-10-01</publish_date>
      <description>An in-depth look at creating applications 
      with XML.</description>
   </book>
```

and the output of discover for this xml would be.

```
{
  "/catalog": [],
  "/catalog/book": "id",
  "/catalog/book/author": [],
  "/catalog/book/title": [],
  "/catalog/book/genre": [],
  "/catalog/book/price": [],
  "/catalog/book/publish_date": [],
  "/catalog/book/description": []
}
```
and you would alter the file to something like the one at the begining of the Mapping section. 

# Importing

To start an import, in your project run python manage.py import [xml_file_name]

```
{
    "root": {
        "file": ["posts.xml"],
        "tag" : ["item"],
        "model": ["PostPage"]
    },
    "title": ["title", "required"],
    "link": [],
    "pubDate": [],
    "dc:creator": [],
    "guid": [],
    "description": [],
    "content:encoded": ["html", "required"],
    "excerpt:encoded": [],
    "wp:post_id": ["wp_post_id"],
    "wp:post_date": [],
    "wp:post_date_gmt": [],
    "wp:comment_status": [],
    "wp:ping_status": [],
    "wp:post_name": ["slug", "required"],
    "wp:status": [],
    "wp:post_parent": [],
    "wp:menu_order": [],
    "wp:post_type": ["wp_post_type"],
    "wp:post_password": [],
    "wp:is_sticky": [],
    "category": "domain,nicename",
    "wp:postmeta": [],
    "wp:postmeta/wp:meta_key": [],
    "wp:postmeta/wp:meta_value": []
  }
```