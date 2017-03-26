## Qgs-datasource-manager
A class to manage datasource path stored in QGIS xml project file

Usage :

```python
from qdsm import QgsProjects

#Provide a list of folder root to process
folders = ["root1", "root2"]

#Initialize the class will list all qgs files contained in the submited folders list
projects = QgsProjects(folders)

#Then we can access to a list of qgs project, but xml are not yet parsed
print(len(projects))
for qgs in projects:
	print(qgs.path, len(qgs.sources))

#Read qgs xml to extract datasource paths
projects.read(verbose=False)

#Iterate
for qgs in projects:
	print(qgs.path)
	for src in qgs:
		print(' >> ' + src.path)

#dump into a text file the list of datasource per projects
projects.dump("path//to/sources.txt")

#Get a list of unique source
uniqueSrc = projects.getUniqueSources()
uniqueSrc.sort()
print(str(len(uniqueSrc)) + ' unique sources')
#Iterate
for src in uniqueSrc:
	#Here filter qgis composer sources
	if src.composer == True:
		print(src.path, src.exists)

#Dump to text file
uniqueSrc.dump("/path/to/sources.txt", sep='\t', filtr={'composer':True})

#Get list of extension
print(uniqueSrc.getExtList())

#Convert datasource path to absolute and save qgs files
projects.toAbs(verbose=True)

#Convert datasource path to relative and save qgs files
projects.toRel(verbose=True)

#Submit a reference file to update datasource paths
#swap file is just a text file in the form:
#/old/path/to/datasource;/new/path/to/datasource
projects.swap("/path/to/swap.txt", sep=';', writeRelPath=True, verbose=True)
```
