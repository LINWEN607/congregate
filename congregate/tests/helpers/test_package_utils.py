import unittest
from pytest import mark
from congregate.helpers.package_utils import *


@mark.unit_test
class PackageUtilsTests(unittest.TestCase):
    def test_pkg_info(self):
        self.maxDiff = None
        with open("congregate/tests/data/pkg-info.example", 'r') as f:
            pkg_info = f.read()
        
        expected_metadata = {
            "author": "John Doe",
            "author_email": "jdoe@example.com",
            "classifier": "Programming Language :: Python :: 3.12",
            "description_content_type": "text/markdown",
            "home_page": "https://gitlab.com/",
            "license": "MIT",
            "metadata_version": "2.1",
            "name": "sample_package",
            "requires_dist": "xlsxwriter (>=3.1.2,<4.0.0)",
            "requires_python": ">=3.8.0",
            "summary": "A sample Python Project",
            "version": "0.1.0",
            "description": """# Example Python Package

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam ac tortor erat. 
Nam blandit cursus eros malesuada faucibus. 
Nunc a nisi felis. Curabitur tempus odio malesuada metus accumsan, id blandit orci gravida. 

Duis auctor, libero at tempus egestas, elit erat porttitor nulla, ac placerat orci eros non arcu. 
Aliquam in maximus nisi, eu ornare erat. Ut rutrum, nunc eget mattis semper, massa justo iaculis leo, vel viverra enim arcu vitae dolor. 
Cras et velit nec orci cursus ornare ac id nibh. 

Ut blandit mauris et consequat luctus. 
Curabitur leo velit, ullamcorper fringilla tempor eu, imperdiet sit amet leo. 
Interdum et malesuada fames ac ante ipsum primis in faucibus. 
Sed imperdiet ex et magna elementum, sit amet viverra tortor vulputate. 
Mauris in orci et urna fringilla vulputate in vitae nulla. 
Nunc vel libero pulvinar, tempor urna et, hendrerit nibh.

## Heading

- Nunc consectetur dolor vitae est lacinia, in vulputate ipsum fringilla
- Sed accumsan feugiat dui id varius. Aenean imperdiet feugiat neque eget vulputate
- Duis non tortor tristique, tempor dui nec, ornare massa
- Suspendisse hendrerit tortor sit amet risus euismod aliquet
- Maecenas et nisl quis felis accumsan tempus. Vestibulum sed porta lectus, non ultricies nisi
- Donec ultricies tempor quam, vitae consectetur purus interdum et
- Nullam id lacinia augue, vitae viverra nibh. Donec egestas felis et hendrerit ornare
- Quisque pellentesque, nulla sed congue cursus, nibh ligula gravida mi, sed elementum tortor nisl sit amet nisi
- Pellentesque sodales ultrices porta. Morbi et metus consequat, ultricies mi nec, porta diam
- Sed sit amet ligula nec velit varius malesuada eu et ex
- Aenean accumsan lacus a ipsum tristique eleifend

"""
        }
        actual_metadata = extract_pypi_package_metadata(pkg_info)

        self.assertDictEqual(actual_metadata, expected_metadata)
