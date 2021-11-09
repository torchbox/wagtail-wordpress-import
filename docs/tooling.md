# Developer Tooling Commands

- [Developer Tooling Commands](#developer-tooling-commands)
  - [Reduce XML command](#reduce-xml-command)
  - [Analyse XML command](#analyse-xml-command)
  - [Delete imported page command](#delete-imported-page-command)
  - [Useful django shell commands](#useful-django-shell-commands)
    - [Delete all imported images](#delete-all-imported-images)
    - [Delete all imported documents](#delete-all-imported-documents)
  - [Errors while running an import](#errors-while-running-an-import)
  - [Databases](#databases)

Wagtail Wordpress Import makes it easy to work with the raw data by providing a set of command line tools.

## Reduce XML command

This is a command to help you reduce the amount of data that needs to be parsed and imported.

```bash
python manage.py reduce_xml path/to/your/xmlfile.xml
```

It will remove all items of `<wp:comment>`. These xml tags represent comments.

The original file is preserved and a new file is created with `-reduced` appended to the file name.

---

## Analyse XML command

This is a command to help you analyse the data you will be importing.

```bash
python manage.py analyze_html_content path/to/your/xmlfile.xml
```

It will generate a table output in the console to show inline styles, HTML tags and shortcodes used to format the content.

---

## Delete imported page command

When testing imports you may need to delete the imported pages and run the import again.

```bash
python manage.py delete_imported_pages [app] [page_model]
# app and page_model are required arguments
```

This script will run until all pages have been deleted and displays the  progress in the console.

## Useful django shell commands

To start the django shell run

```bash
python manage.py shell
```

The commands below are destructive, there's no going back!

### Delete all imported images

```python
from wagtail.images.models import Image
```

```python
Image.objects.all().delete()
```

### Delete all imported documents

```python
from wagtail.documents.models import Document
```

```python
Document.objects.all().delete()
```

## Errors while running an import

When running an import you may encounter errors in the console.

If the import starts and stops with the error `'NoneType' object has no attribute '_inc_path'` then you should try running the following command.

```python
python manage.py fixtree
```

This command scans for errors in your database and attempts to fix any issues it finds.

---

## Databases

SQLITE3

If you are testing your import with an sqlite3 database, try to avoid making any changes in the Wagtail admin while a import is running. 

The import process executes many save actions as it runs and you will likely create a lock on the database if you try to save updates in the Wagtail admin.

This will prevent the import process from completing a save or update.

Using a postgres or mysql database avoids this situation.
