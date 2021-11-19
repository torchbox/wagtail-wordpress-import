# Developer Tooling Commands

- [Developer Tooling Commands](#developer-tooling-commands)
  - [Reduce XML command](#reduce-xml-command)
  - [Analyse XML commands](#analyse-xml-commands)
    - [analyze_html_content](#analyze_html_content)
    - [analyze_xml_content](#analyze_xml_content)
  - [Delete imported page command](#delete-imported-page-command)
  - [Useful Django shell commands](#useful-django-shell-commands)
    - [Delete all images](#delete-all-images)
    - [Delete all documents](#delete-all-documents)
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

## Analyse XML commands

These commands help you analyse the XML data source.

### analyze_html_content

Will generate a table output in the console to show inline styles, HTML tags and shortcodes used in the `<content:encoded>` XML tag.

```bash
python manage.py analyze_html_content path/to/your/xmlfile.xml
```

### analyze_xml_content

Will generate a JSON file your project which shows the structure of all unique XML tags and attributes.

```bash
python manage.py analyze_xml_content path/to/your/xmlfile.xml
```

---

## Delete imported page command

When testing imports you may need to delete the imported pages and run the import again.

```bash
python manage.py delete_imported_pages [app] [page_model]
# app and page_model are required arguments
```

This script will run until all pages of [app].[model] have been deleted and displays the progress in the console.

**WARNING:** It will also delete any pages you have created in the Wagtail admin.

## Useful Django shell commands

To start the Django shell run

```bash
python manage.py shell
```

### Delete all images

**WARNING:** This command is destructive and will delete all images, there's no going back!

```python
from wagtail.images.models import Image
```

```python
Image.objects.all().delete()
```

### Delete all documents

**WARNING:** This command is destructive and will delete all documents, there's no going back!

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

Using a postgres or MySQL database avoids this situation.
