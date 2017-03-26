# -*- coding:utf-8 -*-

INFOS = {
	'author':'domlysz',
	'author_contact':'domlysz@gmail.com',
	'organization':'Entente Causses Cévennes',
	'org_contact':'observatoire@causses-et-cevennes.fr',
	'version':'0.1',
	'date':'april 2017',
	'python':'3.5',
	'ext_deps':[],
	'license':'GPL3'
}


import os
from xml.etree import ElementTree as etree


#provide a list of extension to manually define what kind of path can be edited
#its a security to avoid breaking non-file paths like w*s service or remote database urls
VALID_EXT = [
'.shp', '.tab', '.dxf',
'.osm', '.kml', '.gml', '.gpx', '.geojson',
'.tif', '.tiff', '.jpg', '.jpeg', '.png', '.jp2', '.ecw', '.vrt',
'.gpkg', '.sqlite', '.db', '.mbtiles'
'.csv', '.txt', '.xls', '.xlsx', '.ods',
'.pdf', '.svg'
]


class QgsProjects():
	'''Represent a container of qgis projects'''

	def __init__(self, folders):
		self.folders = folders
		self.projects = []
		#list all qgs files contained in the submited folders list
		for rootdir in self.folders:
			for root, subFolders, files in os.walk(rootdir):
				projects = [f for f in files if f[-4:] == '.qgs']
				for name in projects:
					projectPath = root + os.sep + name
					projectPath = projectPath.replace('\\', '/')#backslash to slash
					self.projects.append(QgsProject(projectPath))

	def __iter__(self):
		return iter(self.projects)

	def __repr__(self):
		return '\n'.join([prj.path for prj in self.projects])

	def __len__(self):
		return len(self.projects)

	def pProgress(self, i, n, percent=False):
		'''progress bar'''
		#Writing '\r' will move the cursor back to the beginning of the line
		#specify empty end character to avoid default newline of print function
		if percent:
			print('\rProgress : ' + str(((i+1)*100)/n), end='%')
		else:
			print('\rProgress : ' + str(i+1)+'/'+str(n), end='')
		if i+1 == n: print('')#will print a newline

	def read(self, verbose=False):
		'''parse all qgs projects'''
		for i, qgs in enumerate(self.projects):
			if not verbose:
				self.pProgress(i, len(self.projects))
			qgs.read(verbose=verbose)

	def toAbs(self, verbose=False):
		'''convert all project's datasource paths to absolute'''
		for qgs in self.projects:
			if not verbose:
				self.pProgress(i, len(self.projects))
			qgs.toAbs(verbose=verbose)

	def toRel(self, verbose=False):
		'''convert all project's datasource paths to relative'''
		for qgs in self.projects:
			if not verbose:
				self.pProgress(i, len(self.projects))
			qgs.toRel(verbose=verbose)

	def swap(self, swapFile, sep=';', writeRelPath=False, verbose=False):
		'''process all project's datasource paths and update location if needed'''
		for qgs in self.projects:
			if not verbose:
				self.pProgress(i, len(self.projects))
			qgs.swap(swapFile, sep, writeRelPath, verbose=verbose)

	@property
	def parsed(self):
		return all([prj.parsed for prj in self.projects])

	def dump(self, output, sep='\t'):
		with open(output, 'w', encoding='utf-8') as f:
			#Select attributes of the datasource that will be dumped
			prjAttr = ['path', 'absolutePath']
			srcAttr = ['composer', 'path', 'subset', 'exists', 'dtype', 'provider', 'layer']
			#write columns header
			f.write(sep.join(prjAttr+srcAttr) + '\n')
			#iterate and write
			for prj in self.projects:
				for src in prj:
					prjProps = [str(getattr(prj, attr, '')) for attr in prjAttr]
					srcProps = [str(getattr(src, attr, '')) for attr in srcAttr]
					f.write(sep.join(prjProps+srcProps) + '\n')

	def getUniqueSources(self):
		'''return unique sources'''
		return QgsSources(self)


class QgsSources():
	'''A container of unique source list'''

	def __init__(self, projects):
		'''extract unique source list from a QgsProjects object'''
		self.sources = []
		for prj in projects:
			for src in prj.sources:
				#not well optimized but we don't expect billions of sources here...
				if src.path not in [src.path for src in self.sources]:
					self.sources.append(src)

	def __iter__(self):
		return iter(self.sources)

	def __repr__(self):
		return '\n'.join([src.path for src in self.sources])

	def __len__(self):
		return len(self.sources)

	def sort(self):
		self.sources.sort()

	def dump(self, output, sep='\t', filtr={}):
		with open(output, 'w', encoding='utf-8') as f:
			srcAttr = ['composer', 'path', 'exists', 'dtype', 'provider']
			f.write(sep.join(srcAttr) + '\n')
			for src in self.sources:
				if not filtr or any([getattr(src, k, None) == v for k, v in filtr.items()]):
					srcProps = [str(getattr(src, attr, '')) for attr in srcAttr]
					f.write(sep.join(srcProps) + '\n')

	def getExtList(self):
		#return set([os.path.splitext(src.path)[1] for src in self.sources])
		'''return a dict of founded extension as keys and the number of occurence as values'''
		d = {}
		for src in self.sources:
			ext = os.path.splitext(src.path)[1]
			if ext in d:
				d[ext] += 1
			else:
				d[ext] = 1
		return d


class QgsProject():
	'''Represent a qgis project as datasouces container'''

	def __init__(self, path):
		self.path = path
		self.sources = []
		self.absolutePath = None
		self.parsed = False

	def __iter__(self):
		return iter(self.sources)

	def __repr__(self):
		return self.path + '\n\t' + '\n\t'.join([src.path for src in self.sources])

	def __len__(self):
		return len(self.sources)

	#####################
	def _backslash2slash(self, path):
		'''convert backslash to slash to make the path usuable both on dos and unix'''
		return path.replace('\\', '/')

	def _pathToAbs(self, path):
		'''Normalize a source path as absolute link'''
		#relative path to absolute
		if path.startswith('.'):
			path = os.path.normpath(os.path.dirname(self.path) + os.sep + path)
		return self._backslash2slash(path)

	def _pathToRel(self, path):
		'''absolute path to relative path'''
		if not path.startswith('.'):
			try:
				path = os.path.relpath(path, os.path.dirname(self.path))
			except ValueError:
				#happen on dos when the 2 submited path do not share the same drive letter
				pass
		return self._backslash2slash(path)

	def _pathSwap(self, path, swapDict):
		'''swap a path following a reference dictionnary
		input path must be an absolute path
		output path will be an absolute path'''
		path = swapDict.get(self._backslash2slash(path), path)
		return self._backslash2slash(path)

	#####################
	def read(self, verbose=False):
		'''parse the xml file'''
		self._parse(verbose=verbose)

	def toAbs(self, verbose=False):
		'''convert all source paths to absolute'''
		self._parse(write=True, verbose=verbose)

	def toRel(self, verbose=False):
		'''convert all source paths to relative'''
		self._parse(write=True, writeRelPath=True, verbose=verbose)

	def swap(self, swapFile, sep=';', writeRelPath=False, verbose=False):
		'''process all source paths and update location if needed'''
		#Extract swap file to dictionnary
		swapDict = {}
		with open(swapFile, 'r',  encoding='utf-8') as f:
			for line in f:
				line = line.strip()
				if line == '':
					continue
				src, dst = line.split(sep)
				swapDict[src] = dst
		self._parse(write=True, writeRelPath=writeRelPath, swapDict=swapDict, verbose=verbose)

	#####################

	def _parse(self, write=False, writeRelPath=False, swapDict={}, verbose=False):
		'''
		Parse a qgs xml file to build a list of datasource (QgsSource class)
		extracted paths are always converted to absolute and slashed paths
		if 'write' is True then the xml tree will be saved with these absolute paths
		unless 'writeRelPath' is True, in this case paths will be converted to relative beforehand
		If a swap dictionnary is passed then it will be used to update paths location
		'''

		if verbose:
			print('Parsing ' + self.path)

		with open(self.path, 'r', encoding='utf-8') as f:
			try:
				tree  = etree.parse(f)
			except:
				if verbose:
					print(' * File cannot be parsed')
				return

			rootTree = tree.getroot()

			#Get project path mode property
			if rootTree.find('.//properties/Paths/Absolute').text == 'true':
				self.absolutePath = True
			else:
				self.absolutePath = False

			##################
			#Get composer ressources (image, svg...)
			if verbose: print('  > Composer ressources')
			for elem in rootTree.findall('.//Composer/Composition/ComposerPicture'):
				#get normalized path
				srcPath = self._pathToAbs(elem.attrib['file'])
				srcExt = os.path.splitext(srcPath)[1]
				if verbose: print('    - ' + srcPath)
				#build source properties dictionnary
				srcProps = {}
				srcProps['composer'] = True
				#Append in sources list as QgsSource object
				src = QgsSource(srcPath, **srcProps)
				self.sources.append(src)
				#xml edits
				if write:
					if swapDict:
						srcPath = self._pathSwap(srcPath, swapDict)
						if srcPath != src.path:
							src.path = srcPath #update QgsSource
							if verbose: print('    <-> Swap to ' + srcPath)
					if writeRelPath:
						srcPath = self._pathToRel(srcPath)
					#edit tree
					elem.attrib['file'] = srcPath

			##################
			#Get layers datasources
			if verbose: print('  > Map layer datasource')
			for elem in rootTree.findall('.//projectlayers/maplayer'):
				srcProps = {}
				srcProps['composer'] = False

				#Get provider
				try:
					srcProps['provider'] = elem.find('provider').text
				except:
					print('pass layer node with no provider')
					continue

				#Get datasource url
				try:
					srcPath = elem.find('datasource').text
					srcExt = None #do not except it easily
				except:
					print('pass layer node with no datasource')
					return

				#Get some others properties
				srcProps['dtype'] = elem.attrib["type"]
				srcProps['layer'] = elem.find('layername').text
				srcProps['subset'] = '' #org filter

				#for now only edit datasource using gdal/org provider
				#TODO handle other file based provider like
				#  >delimitedtext: file:\Z:\data\file.csv?type=csv&geomType=none
				#  >spatialite : dbname='/home/data/file.sqlite' table="tst" (geometry) sql=
				#  >gpx, virtual...
				# for each provider we must be able to parse the datasource path and then reconstruct it if needed
				if srcProps['provider'] in ['ogr', 'gdal']:
					#we want to process only files based path not db or wms url
					#but we can't just test if file exists because the path link can be outdated
					#so just check if its a valid extension
					if '|' in srcPath: #org filter in path
						srcPath, srcProps['subset'] = srcPath.split('|', 1)
					srcExt = os.path.splitext(srcPath)[1]
					if srcExt in VALID_EXT:
						#get normalized path
						srcPath = self._pathToAbs(srcPath)

				#Append in sources list as QgsSource object
				if verbose: print('    - ' + srcPath)
				src = QgsSource(srcPath, **srcProps)
				self.sources.append(src)

				#xml edits
				if write and srcProps['provider'] in ['ogr', 'gdal'] and srcExt in VALID_EXT:
					if swapDict:
						srcPath = self._pathSwap(srcPath, swapDict)
						if srcPath != src.path:
							src.path = srcPath #update QgsSource
							if verbose: print('    <-> Swap to ' + srcPath)
					if writeRelPath:
						srcPath = self._pathToRel(srcPath)
					#edit tree
					if srcProps['subset'] is None:
						elem.find('datasource').text = srcPath
					else:
						elem.find('datasource').text = srcPath + '|' + srcProps['subset']

				self.parsed = True

			##################
			#Write xml file
			if write:
				#update project path mode setting and QgsProject attribute
				if writeRelPath:
					if verbose: print('>> Saving with relative paths')
					rootTree.find('.//properties/Paths/Absolute').text = 'false'
				else:
					if verbose: print('>> Saving with absolute paths')
					rootTree.find('.//properties/Paths/Absolute').text = 'true'
				self.absolutePath = not(writeRelPath)
				#save xml
				tree.write(self.path)

			if verbose: print('\n')


class QgsSource():
	'''
	Attributes model:
	path : absolute path of the datasource
	composer : bool, flag if the source is a composer ressource or not
	subset : the filter apply on the datasource at qgis ogr provider level
	dtype : vector, raster, database, w*s ...
	provider : qgis provider name [gdal, ogr, delimitedtext, postgres, spatialite, virtual, memoy, grass, gpx, wfs, wms...]
	layer : the layer name in qgis toc
	'''

	def __init__(self, path, **kwargs):
		self.path = path
		for k, v in kwargs.items():
			setattr(self, k, v)

	def __repr__(self):
		return self.path

	def __lt__(self, other):
		return self.path.lower() < other.path.lower()

	@property
	def exists(self):
		return os.path.exists(self.path)
