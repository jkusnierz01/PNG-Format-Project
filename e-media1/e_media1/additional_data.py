
SIGNATURE = b'\x89PNG\r\n\x1a\n'
 

EXIF_TAGS = {
    270: ['ImageDescription', 'string'],
    271: ['Make', 'string'],
    272: ['Model', 'string'],
    274: ['Orientation', 'digit'],
    282: ['XResolution', 'rational'],
    283: ['YResolution', 'rational'],
    296: ['ResolutionUnit', 'digit'],
    305: ['Software', 'string'],
    306: ['DateTime', 'string'],
    318: ['WhitePoint', 'rational'],
    319: ['PrimaryChromaticities', 'rational'],
    529: ['YCbCrCoefficients', 'rational'],
    531: ['YCbCrPositioning', 'digit'],
    532: ['ReferenceBlackWhite', 'rational'],
    33432: ['Copyright', 'string'],
    34665: ['ExifOffset', 'digit'],      
    # SUB TAGS
    33434: ['ExposureTime', 'rational'],
    33437: ['FNumber', 'rational'],
    34850: ['ExposureProgram', 'digit'],
    34855: ['ISOSpeedRatings', 'digit'],
    36864: ['ExifVersion', 'string'],
    36867: ['DateTimeOriginal', 'string'],
    36868: ['DateTimeDigitized', 'string'],
    37121: ['ComponentsConfiguration', 'string'],
    37122: ['CompressedBitsPerPixel', 'rational'],
    37377: ['ShutterSpeedValue', 'rational'],
    37378: ['ApertureValue', 'rational'],
    37379: ['BrightnessValue', 'rational'],
    37380: ['ExposureBiasValue', 'rational'],
    37381: ['MaxApertureValue', 'rational'],
    37382: ['SubjectDistance', 'rational'],
    37383: ['MeteringMode', 'digit'],
    37384: ['LightSource', 'digit'],
    37385: ['Flash', 'digit'],
    37386: ['FocalLength', 'rational'],
    37510: ['UserComment', 'string'],
    40960: ['FlashPixVersion', 'string'],
    40961: ['ColorSpace', 'digit']         # 0xaa001
}

data_format_bytes = {
    1: 1,  # unsigned byte
    2: 1,  # ascii strings
    3: 2,  # unsigned short
    4: 4,  # unsigned long
    5: 8,  # unsigned rational
    6: 1,  # signed byte
    7: 1,  # undefined
    8: 2,  # signed short
    9: 4,  # signed long
    10: 8, # signed rational
    11: 4, # single float
    12: 8  # double float
}


color_type_bytes = {
    0:1,
    2:3,
    3:1,
    4:2,
    6:4
}