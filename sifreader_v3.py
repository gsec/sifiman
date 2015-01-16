import numpy as N

def _data_withAndorSIF(info):
    """use this to get 'spiffed up' array"""

    import weakref
    #NOT-WORKING:  self.data.Mrc = weakref.proxy( self )

    #20071123: http://www.scipy.org/Subclasses
    class ndarray_inSIFfile(N.ndarray):
        def __array_finalize__(self,obj):
            self.AndorSIF = getattr(obj, 'AndorSIF', None)

    data = info.imageData
    data.__class__ = ndarray_inSIFfile
    ddd = weakref.proxy( data )
    info.imageData = ddd
    data.AndorSIF = info

    return data


def readSIF(fn, read_Back_ref=0):
    """
    TODO FIXME -- only read_Back_ref=0 supported

    if read_Back_ref 
      == 0: read only data
      == 1: read data + back
      == 2: read data + back + ref

    #old:returns tuple if read_Back_ref >0

    return memmapped ndarray with "special AndorSIF" attribute

    %  [data,back,ref]=sifread(file)
    %     Read the image data, background and reference from file.
    %     Return the image data, background and reference in named
    %     structures as follows:
    %
    %  .temperature            CCD temperature [#C]
    %  .exposureTime           Exposure time [s]
    %  .cycleTime              Time per full image take [s]
    %  .accumulateCycles       Number of accumulation cycles
    %  .accumulateCycleTime    Time per accumulated image [s]
    %  .stackCycleTime         Interval in image series [s]
    %  .pixelReadoutTime       Time per pixel readout [s]
    %  .detectorType           CCD type
    %  .detectorSize           Number of read CCD pixels [x,y]
    %  .fileName               Original file name
    %  .shutterTime            Time to open/close the shutter [s]
    %  .frameAxis              Axis unit of CCD frame
    %  .dataType               Type of image data
    %  .imageAxis              Axis unit of image
    %  .imageArea              Image limits [x1,y1,first image;
    %                                        x2,y2,last image]
    %  .frameArea              Frame limits [x1,y1;x2,y2]
    %  .frameBins              Binned pixels [x,y]
    %  .timeStamp              Time stamp in image series
    %  .imageData              Image data (x,y,t)

    translated from matlab sifread.m  by Marcel Leutenegger (c) November 2006
    """
    f = open(fn, "rb")
    l = f.readline()[:-1]
    if l != 'Andor Technology Multi-Channel File':
        raise IOError, 'Not an Andor SIF image file.'

    f.readline() #skipLine # 65538 1

    data,next = readSection(f)
    ###pi#debug#return data,next


    #fix postponed image data -- use memmap
    qm=N.memmap(fn, mode="r")
    md = qm[data.imageData[0]:data.imageData[0]+4*data.imageData[1]]
    q = md.view(N.single)
    q.shape = data.imageData[2]
    data.imageData = q

    # FIXME TO read
    '''
    if next and read_Back_ref>0:
        back,next = readSection(f)
        if next and read_Back_ref>1:
            ref,next = readSection(f)
            return data,back,ref
        else:
            return data,back            
    else:
        return data
    '''

    return _data_withAndorSIF(data), next


def readSection(f):
    """
    % f      File handle

    returns
    % info   Section data
    % next   Flags if another section is available
    """
    class _info:
        def __getitem__(s, k):
            return s.__get_attribute__(k)
        def __str__(s):
            return """exposureTime[sec]: %(exposureTime)s
cycleTime[sec]: %(cycleTime)s
accumulateCycles: %(accumulateCycles)s
accumulateCycleTime[sec]: %(accumulateCycleTime)s
stackCycleTime[sec]: %(stackCycleTime)s
pixelReadoutTime[sec]: %(pixelReadoutTime)s
shutterTime[sec]: %(shutterTime)s
temperature[C]: %(temperature)s\
"""%s.__dict__
        #def _get_keys(s):
        #    return s.__dict__
    info= _info()
    s = f.readline().split()
    info.temperature = float(s[5]) # int(s[5])

    if len(s)<13: # check 
        s += ['hack'] + f.readline().split()

    info.exposureTime=float(s[12])
    info.cycleTime=float(s[13])
    info.accumulateCycleTime=float(s[14])
    info.accumulateCycles=float(s[15])

    info.stackCycleTime=float(s[17])
    info.pixelReadoutTime=float(s[18])

    info.gainDAC=int(s[21])

    #skip read of line --- seb: last number is length of next string
    # seb
    # sebinfo.detectorType = f.readline().rstrip()
    n=int(s[-1])
    info.detectorType = f.read(n)
    f.readline() # skip rest of line

    s = f.readline().split()
    info.detectorSize=map(int, s[:2])
    n=int(s[-1])
    info.fileName = f.read(n)
    f.readline() # skip rest of line (just a space and \n")

    for _ in range(3):
        f.readline() # skip rest of line

    f.read(14) # skip 14 bytes
    s = f.readline().split()
    #pi# info.shutterTime=map(float, s[:2])

    '''
Andor Technology Multi-Channel File 
65538 1 
65566 0 0 1 1375771748 -40 ^@ ^@ ^@ ^A ^@ 0 0.1 0.17061 0.17061 1 ^@ 0.17061 2e-07 0 1 0 0 0 1e-08 0 0 ^D ^@ 1 0 4 1 0 0 0 0 0 0 0 0 1.3e-05 0 1 0 0 1 -999 1 0 0 0 0 -1 4 20 30007 0 0 1 1000 0 0 0 550 0 0 0 0 0 0 0 0 0 1 1 5 
DV887  
 512 512 217 
\\Mamba\q\data\AG_Hecht_Sample_Log_File\2013-06-20_Pi-130620-BlueBoxAle_TWTL-Transfer-Xiaofei\130806-pgeisler-SuperK_TWTL-after-retransfer\F001-ADM1133-01MS_WL800nm-100nW-PolIn000-PolOutNon-PolRot270_BBneuCr150-IM.sif
65538 2048



65538 ^A ^B ^C ^@ 0 0                                                                                                  
65540 0 0 500 0 0 1200 1200                                                                                            
0 10
0 0 0 0 0  0 0 0 0 0 0 10
0 SR303i
0 10
0 10
0 0  
65536 1 500 200
5 SR163        
65538 0 0 0 0 0 0 0 0 0 0 0 0 0
0 0 0 0  
0 0 0 0
0 0 0 0
0 0 0 

-1
65539 ^A ^@ ^A ^@ ^A ^@                                                                                                
0 1 0 0                                                                                                                
0 1 0 0                                                                                                                
0 1 0 0                                                                                                                
422
16
16
12
Pixel number6                                                                                                          
Counts12                                                                                                               
Pixel number65541 1 512 512 1 1 1 262144 262144                                                                        
65538 1 512 512 1 1 1 0                                                                                                
         0                                                                                                             
0
    '''

    #pi# seek till 65539
    s = f.readline()
    ##while not (s.startswith('65539')):# or s.startswith('65540')):
    while not s.startswith('65540'):
    #while not s[:5] == '65539':
        s = f.readline()
    s = f.readline()
    while not s.startswith('65540'):
        s = f.readline()
    #pi# seek till 65539
    ##for _ in range(6):#pi#8
    for _ in range(7):#pi#8
        f.readline() # skip rest of line

    if 'Luc' == info.detectorType:
        #% Andor Luca
        f.readline() # skip rest of line
        f.readline() # skip rest of line


    s = f.readline().split()
    n=int(s[-1])
    info.frameAxis = f.read(n) # "Pixel number"

    s = f.readline().split()
    n=int(s[-1])
    info.dataType = f.read(n)  # "Counts"
    
    s = f.readline().split()
    n=int(s[-1])
    info.imageAxis = f.read(n) # "Pixel number"
    

    s = f.readline().split()
    #pi#assert int(s[0]) == 65538
    assert int(s[0]) == 65541 #pi#

    #info.imageArea = map(int, s[1:7])
    o = map(int, s[1:7])
    info.imageArea = N.array(((o[0],o[3],o[5]),(o[2],o[1],o[4])))
    sizeStack = int(s[7])
    size2dSect = int(s[8])
    
    s = f.readline().split()
    assert int(s[0]) == 65538

    o=map(int, s[1:5])
    info.frameArea=N.array(((o[0],o[3]),(o[2],o[1])))
    o=map(int, s[5:7])
    info.frameBins=N.array((o[1],o[0]))
    info.frameBins=N.array((1,1))


    shape2d=tuple((1 + N.diff(info.frameArea, axis=0))[0]//info.frameBins)
    nSects=(1 + N.diff(info.imageArea[:,2]))[0]
    if N.prod(shape2d) != size2dSect or size2dSect*nSects != sizeStack:
        raise IOError, 'Andor SIF: Inconsistent image header.'

    shape3d = (nSects,)+shape2d

    info.comment_ = []
    for n in range(nSects):
        s = f.readline().split()
        n=int(s[-1])
        if n:
            info.comment_.append(str(n)+f.read(n))
        f.readline() # skip rest of line


    info.timeStamp=N.fromfile(f, N.uint16, 2) # 4 bytes to be read here !!! seb
    #qqqq = N.fromfile(f, N.uint8, 2)


    ##return U.localsAsOneObject()
    #info.imageData=N.fromfile(f, N.single, sizeStack) #N.prod(shape2d)*nSects) # =>single'),[s z]);
    ##info.imageData=reshape(fread(f,prod(s)*z,'single=>single'),[s z]);
    #info.imageData.shape = shape3d

    #just save file-position, numberOfPixels, shape
    #then seek for now,  reopen with memmap later
    info.imageData=(f.tell(), sizeStack, shape3d)
    f.seek(sizeStack*4, 1)

    s = f.readline().split()
    n=int(s[-1])
    if n:
        s = f.read(n)
        print s  # ???

    s = f.readline().split()
    next =int(s[0])
    #o=readString(f);           % ???
    #if numel(o)
    #   fprintf('%s\n',o);      % ???
    #end
    #next=fscanf(f,'%d',1);


    return info, next

    '''
    #offset 0
    o=fscanf(f,'%d',6);
    info.temperature=o(6);
    skipBytes(f,10);
    o=fscanf(f,'%f',5);
    info.exposureTime=o(2);
    info.cycleTime=o(3);
    info.accumulateCycleTime=o(4);
    info.accumulateCycles=o(5);
    skipBytes(f,2);


    o=fscanf(f,'%f',2);
    info.stackCycleTime=o(1);
    info.pixelReadoutTime=o(2);

    o=fscanf(f,'%d',3);
    info.gainDAC=o(3);
    skipLines(f,1);

    info.detectorType=readLine(f);

    info.detectorSize=fscanf(f,'%d',[1 2]);
    info.fileName=readString(f);
    skipLines(f,3);
    skipBytes(f,14);
    info.shutterTime=fscanf(f,'%f',[1 2]);
    skipLines(f,8);
    if strmatch('Luc',info.detectorType)
       skipLines(f,2);                       % Andor Luca
    end
    info.frameAxis=readString(f);
    info.dataType=readString(f);
    info.imageAxis=readString(f);
    o=fscanf(f,'65538 %d %d %d %d %d %d %d %d 65538 %d %d %d %d %d %d',14);
    info.imageArea=[o(1) o(4) o(6);o(3) o(2) o(5)];
    info.frameArea=[o(9) o(12);o(11) o(10)];
    info.frameBins=[o(14) o(13)];
    s=(1 + diff(info.frameArea))./info.frameBins;
    z=1 + diff(info.imageArea(5:6));
    if prod(s) ~= o(8) | o(8)*z ~= o(7)
       fclose(f);
       error('Inconsistent image header.');
    end
    for n=1:z
       o=readString(f);
       if numel(o)
          fprintf('%s\n',o);      % comments
       end
    end
    info.timeStamp=fread(f,1,'uint16');
    info.imageData=reshape(fread(f,prod(s)*z,'single=>single'),[s z]);
    o=readString(f);           % ???
    if numel(o)
       fprintf('%s\n',o);      % ???
    end
    next=fscanf(f,'%d',1);
    '''
