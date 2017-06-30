#!/usr/bin/env python

# github.com/1adam

import docker, sys

def debugPrint( item ):
    for i in item:
        try:
            print i, client.images.get(i).tags[0]
        except IndexError:
            print "<no tag>"

def findTheInitialParent(ID):
    img = client.images.get(ID)
    if len( img.attrs['Parent'] ) > 0:
          imgParent = client.images.get(img.attrs['Parent'])
          if len(imgParent.tags) == 0:
              return findTheInitialParent(imgParent.id)
          return imgParent.id
    return ID


client = docker.from_env()

DRYRUN=False
DEBUGMODE=False

# number of containers/images to retain (take the latest N from the .list() return value)
# i.e. '2' means keep the latest image/container, and one image/container previous in a given image tag
# (e.g. the 'gsum' in the docker tag 'gsum:1.23')
NTR=2 

if "--help" in sys.argv[1:]:
    print "Usage:"
    print sys.argv[0], "< --help | [--debug] [--noop] >"
    exit()

if "--noop" in sys.argv[1:]:
    DRYRUN=True
    print "*** *** *** ***"
    print "*** DRY RUN ***"
    print "*** *** *** ***"
    print ""

if "--debug" in sys.argv[1:]:
    DEBUGMODE=True

runConts={}
runImgKeep=[]
for rc in client.containers.list():
    if rc.image.tags[0] not in runConts.iterkeys():
        runConts.update( {rc.image.tags[0]: rc.image.id} )
        runImgKeep.append( rc.image.id )

runRepoKeep=[]
for img, id in runConts.iteritems():
    imgName, imgTag = img.split(":")
    for rimg in client.images.list(imgName)[:NTR]:
        runRepoKeep.append( rimg.id )

exitedConts={}
for rc in client.containers.list( filters={ 'status':'exited'} ):
    if rc.image.tags[0] not in exitedConts.iterkeys():
        exitedConts.update( {rc.image.tags[0]: rc.image.id} )

exitedRepoKeep=[]
for img, id in exitedConts.iteritems():
    imgName = img.split(":")[0]
    for i in client.images.list(imgName)[:NTR]:
        imgFound = False
        if id is i.id:
            if (id not in runImgKeep) or (id not in runRepoKeep):
                exitedRepoKeep.append( id )
            else:
                imgFound = True
        if imgFound is False:
            exitedRepoKeep.append( i.id )

preKeepImages = runImgKeep + runRepoKeep + exitedRepoKeep

parentsOfKeepImages = []
for pki in preKeepImages:
    parentId = client.images.get(pki).attrs['Parent']
    if len(parentId) > 0:
        imgParent = findTheInitialParent( parentId )
        if imgParent != '' and imgParent != None:
            if imgParent not in parentsOfKeepImages:
                parentsOfKeepImages.append( imgParent )

keepImages = set( preKeepImages + parentsOfKeepImages )

if DEBUGMODE:
    print "-- *** DEBUG *** --"
    print "runConts:"
    for rcimg, rcid in runConts.iteritems():
        print rcid, rcimg
    print ""
    print "runImgKeep:"
    debugPrint(runImgKeep)
    print ""
    print "runRepoKeep:"
    debugPrint(runRepoKeep)
    print ""
    print "exitedConts:"
    for ecimg, ecid in exitedConts.iteritems():
        print ecid, ecimg
    print ""
    print "exitedRepoKeep:"
    debugPrint(exitedRepoKeep)
    print ""
    print "parentsOfKeepImages:"
    debugPrint(parentsOfKeepImages)
    print ""
    print "- -- --- ---- ----- ---- --- -- -"
    print "keepImages:"
    debugPrint(keepImages)
    print "-- *** END DEBUG *** --"
    print ""

removeImages=set()
for ai in client.images.list():
    if ai.id not in keepImages:
        removeImages.add( ai.id )

removeContainers=set()
for ac in client.containers.list(all=True):
    if ac.image.id not in keepImages:
        removeContainers.add( ac.id )

if len(removeContainers):
    for rc in removeContainers:
        print "Removing container", rc, client.containers.get(rc).name, client.containers.get(rc).image.tags[0], "...",
        if DRYRUN:
            print "(not really)",
        else:
            client.containers.get(rc).remove()
        print "OK"
else:
    print "No containers to remove."

if len(removeImages):
    for ri in removeImages:
        print "Removing image", ri, client.images.get(ri).tags[0], "...",
        if DRYRUN:
            print "(not really)",
        else:
            client.images.remove( ri )
        print "OK"
else:
    print "No images to remove."
