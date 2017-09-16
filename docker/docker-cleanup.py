#!/usr/bin/env python
# github.com/1adam

# let the madness begin.

import sys, argparse, docker, pprint

client = docker.from_env()

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

def main():
    
    parser = argparse.ArgumentParser(description='Clean up old docker images and containers.')
    parser.add_argument('-d', '--debug', action='store_true', dest='DEBUGMODE', help='Enable Debug' )
    parser.add_argument('-n', '--noop', action='store_true', dest='DRYRUN', help='NOOP / Dry Run' )
    parser.add_argument('-v', '--version', action='version', version="That's not polite.", help='Display version' )
    parser.add_argument('-r', '--retain', nargs=1, type=int, default=3, dest='NTR', help='# of images/containers to keep (1 = only the current/latest) per image name (eg. "nginx" in "nginx:latest")' )
    Args = parser.parse_args()

    if Args.DRYRUN:
        print "**** NOOP / Dry Run ****"
    if Args.DEBUGMODE:
        print "DEBUG enabled"
    print "Retaining", Args.NTR, "images/containers"

    runImgs={}
    runConts={}
    keepImagesRunning=set()
    for rc in client.containers.list():
        imgName, imgTag = rc.image.tags[0].split(':')
        imgId = rc.image.id
        contName = rc.name
        contId = rc.id
        keepImagesRunning.add( imgId )
        if imgName not in runImgs.iterkeys():
            runImgs.update( { imgName: { imgTag: imgId } } )
        if imgTag not in runImgs[imgName].iterkeys():
            runImgs[imgName].update( { imgTag: imgId } )
        if contName not in runConts.iterkeys():
            runConts.update( { contName: { 'contId': contId, 'imgId': imgId, 'imgName': imgName, 'imgTag': imgTag } } )
    if Args.DEBUGMODE:
        print "---------"
        pprint.pprint(runImgs)
        print "---------"
        pprint.pprint(runConts)
        print "---------"
        pprint.pprint( keepImagesRunning )
    

    exit(255)




    latestConts={}
    latestContsKeep=[]
    for lc in client.containers.list(limit=Args.NTR):
        if lc.image.tags[0] not in latestConts.iterkeys():
            latestConts.update( { lc.image.tags[0]: lc.image.id } )
            latestContsKeep.append( lc.image.id )

    runConts={}
    runImgKeep=[]
    runningRepos=[]
    for rc in client.containers.list():
        if rc.image.tags[0] not in runConts.iterkeys():
            runConts.update( {rc.image.tags[0]: rc.image.id} )
            runImgKeep.append( rc.image.id )
            runningRepos.append( rc.image.tags[0] )

    runningReposKeep=[]
    for repotag in runningRepos:
        for rimg in client.images.list(name=repotag)[:Args.NTR]:
            runningReposKeep.append( rimg.id )
    
    preKeepImages = runImgKeep + latestContsKeep + runningReposKeep
    
    parentsOfKeepImages = []
    for pki in (preKeepImages):
        parentId = client.images.get(pki).attrs['Parent']
        if len(parentId) > 0:
            imgParent = findTheInitialParent( parentId )
            if imgParent != '' and imgParent != None:
                if imgParent not in parentsOfKeepImages:
                    parentsOfKeepImages.append( imgParent )
    
    keepImages = set( preKeepImages + parentsOfKeepImages )

    if Args.DEBUGMODE:
        print "-- *** DEBUG *** --"
        print "latestConts:"
        for lcimg, lcid in latestConts.iteritems():
            print lcid, lcimg
        print ""
        print "latestContsKeep:"
        debugPrint(latestContsKeep)
        print ""
        print "runConts:"
        for rcimg, rcid in runConts.iteritems():
            print rcid, rcimg
        print ""
        print "runImgKeep:"
        debugPrint(runImgKeep)
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
            if Args.DRYRUN:
                print "(not really)",
            else:
                client.containers.get(rc).remove()
            print "OK"
    else:
        print "No containers to remove."
    
    if len(removeImages):
        for ri in removeImages:
            try:
               iname = client.images.get(ri).tags[0]
            except IndexError:
               iname = "<no tag>"
            print "Removing image", ri, iname, "...",
            if Args.DRYRUN:
                print "(not really)",
            else:
                client.images.remove( ri )
            print "OK"
    else:
        print "No images to remove."

if __name__ == "__main__":
    main()
