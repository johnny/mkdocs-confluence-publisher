from setuptools import setup, find_packages

# Read the contents of your README file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mkdocs-confluence-publisher',
    version='0.3.0',
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'mkdocs>=1.0',
        'atlassian-python-api>=3.14.0',
        'mistune',
        'md2cf',
        'python-dotenv',
        'mermaid-py'
    ],
    entry_points={
        'mkdocs.plugins': [
            'confluence-publisher = mkdocs_confluence_publisher:ConfluencePublisherPlugin',
        ]
    },
    author='Jonas von Andrian',
    author_email='j.andrianmueller@outlook.com',
    description='A MkDocs plugin to publish documentation to Confluence',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/johnny/mkdocs-confluence-publisher',
    project_urls={
        'Bug Tracker': 'https://github.com/johnny/mkdocs-confluence-publisher/issues',
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Documentation',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    license='Apache License 2.0',
    keywords='mkdocs confluence documentation',
    include_package_data=True,
    zip_safe=False,
)
