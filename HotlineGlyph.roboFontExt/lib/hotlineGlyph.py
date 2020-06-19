import os
from AppKit import NSFilenamesPboardType, NSDragOperationCopy, NSDragOperationMove, NSColor
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.tools.textSplitter import splitText

from vanilla import FloatingWindow, Window, List, SquareButton, EditText, CheckBox

from mojo.events import addObserver, removeObserver
from mojo.UI import UpdateCurrentGlyphView, getDefault
from mojo.drawingTools import *
from mojo.pens import DecomposePointPen

from fontTools.ttLib import TTFont
from fontTools.pens.cocoaPen import CocoaPen
from fontTools.ufoLib.glifLib import readGlyphFromString, glyphNameToFileName, GlyphSet



class getListofFiles(BaseWindowController):

    supportedFontFileFormats = ['.ufo', '.otf', '.ttf']

    def __init__(self):
        self.font_order = []
        self.position = "left"
        
        L = 0  # left
        T = 0  # top
        W = 200 # width
        H = 300  # height
        p = 10 # padding
        buttonHeight = 20

        title = "☎️ Hotline Glyph"
        self.w = Window((W, H), title, minSize=(W/3, H/3))

        self.w.fileList = List(
            (L, T, -0, -(p * 3 + buttonHeight * 2)),
            self.font_order,
            columnDescriptions=[
                {"title": "✓", "width":20},
                {"title": "File name"},
                ], # files
            showColumnTitles=False,
            allowsMultipleSelection=True,
            enableDelete=True,
            otherApplicationDropSettings = dict(
                type=NSFilenamesPboardType,
                operation=NSDragOperationCopy,
                callback=self.dropCallback),
            dragSettings=dict(type="RangeType", 
                                callback=self.font_list_drag_callback),
            selfDropSettings=dict(type="RangeType", 
                                operation=NSDragOperationMove, 
                                callback=self.font_list_drop_callback)
            )

        self.w.editText = EditText((p, -(p * 2 + buttonHeight * 2), -p, buttonHeight))

        self.w.draw = CheckBox((p, -(p + buttonHeight), -p, buttonHeight), 'show', value=True, callback=self.updateViewCallback)

        self.w.toLeftbutton = SquareButton((-p*6, -(p + buttonHeight), p*2, buttonHeight), "←", sizeStyle='small', callback=self.toLeft)
        self.w.toRightbutton = SquareButton((-p*3, -(p + buttonHeight), p*2, buttonHeight), "➝", sizeStyle='small', callback=self.toRight)

        addObserver(self, "drawPreviewRef", "drawBackground")
        addObserver(self, "drawRef", "drawPreview")

        self.setUpBaseWindowBehavior() # Needed for the windowCloseCallback

        self.w.open()


    def windowCloseCallback(self, sender):
        removeObserver(self, 'drawBackground')
        removeObserver(self, 'drawPreview')
        self.fileList = []
        super(getListofFiles, self).windowCloseCallback(sender)

    def updateViewCallback(self, sender):
        UpdateCurrentGlyphView()

    def toRight(self, sender):
        self.position = "right"
        UpdateCurrentGlyphView()

    def toLeft(self, sender):
        self.position = "left"
        UpdateCurrentGlyphView()

    def drawPreviewRef(self, info):
        save()
        fillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 0.05)
        fillColor.set()
        self. _drawGlyph(info["glyph"], scale=1, stroke=False)
        UpdateCurrentGlyphView()
        restore()

    def drawRef(self, info):
        save()
        fillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0)
        fillColor.set()
        self. _drawGlyph(info["glyph"], scale=info["scale"])
        UpdateCurrentGlyphView()
        restore()


    def _drawGlyph(self, glyph, stroke=True, scale=1):
        # get settings
        if not self.w.draw.get():
            return

        fileList  = self.w.fileList
        inputText = self.w.editText.get()
        
        if not len(fileList) == 0 and inputText == "":
            return

        cf = CurrentFont()
        cf_upm = cf.info.unitsPerEm
        
        pos = self.position
        
        if pos == "left":
            fileList = reversed(fileList)
        if pos == "right":
            fileList = fileList
        
        save()
        for file_index, file in enumerate(fileList):
            file_path = file["File path"]

            if file_path.endswith('.ufo'):
                # get font
                font = file["Font file"]
                if font is None:
                    return
            if file_path.endswith(('.otf', '.ttf')):
                font = TTFont(file_path)
            
            splittedInputText = self.stringToGlyphs(inputText, file_path, font)

            if pos == "left":
                splittedInputText = reversed(list(splittedInputText))
            if pos == "right":
                splittedInputText = list(splittedInputText)

            
            for inputGlyph_index, inputGlyph in enumerate(splittedInputText):
                glyphName = inputGlyph
                
                if pos == "right":
                    if file_index == 0 and inputGlyph_index == 0:
                        previous_glyphName = CurrentGlyph().name
                        previous_font = CurrentFont()
                        previous_fontPath = CurrentFont().path
                        
                        if previous_fontPath.endswith(".ufo"):
                            previous_glyph = previous_font[previous_glyphName]
                            xOffset = previous_glyph.width
                        if previous_fontPath.endswith(('.otf', '.ttf')):
                            previous_glyph = previous_font.getGlyphSet()[previous_glyphName]
                            xOffset = previous_glyph.width

                    elif file_index == 0 and inputGlyph_index > 0:
                        previous_glyphName = splittedInputText[inputGlyph_index-1]
                        previous_fontPath = fileList[file_index]["File path"]

                        if previous_fontPath.endswith(".ufo"):
                            previous_glyph = fileList[file_index]["Font file"][previous_glyphName]
                            xOffset = previous_glyph.width
                        if previous_fontPath.endswith(('.otf', '.ttf')):
                            previous_glyph = fileList[file_index]["Font file"].getGlyphSet()[previous_glyphName]
                            # previous_glyph = font.getGlyphSet()[previous_glyphName]
                            xOffset = previous_glyph.width
                            

                    elif file_index > 0 and inputGlyph_index == 0:
                        previous_glyphName = splittedInputText[-1]
                        previous_font = fileList[file_index-1]["Font file"]
                        previous_fontPath = fileList[file_index-1]["File path"]

                        if previous_fontPath.endswith(".ufo"):
                            previous_glyph = previous_font[previous_glyphName]
                            xOffset = previous_glyph.width
                        if previous_fontPath.endswith(('.otf', '.ttf')):
                            previous_glyph = previous_font.getGlyphSet()[previous_glyphName]
                            xOffset = previous_glyph.width

                            

                    if file_index > 0 and inputGlyph_index > 0:
                        previous_glyphName = splittedInputText[inputGlyph_index-1]
                        previous_fontPath = fileList[file_index]["File path"]

                        if previous_fontPath.endswith(".ufo"):
                            previous_glyph = fileList[file_index]["Font file"][previous_glyphName]
                            xOffset = previous_glyph.width
                        if previous_fontPath.endswith(('.otf', '.ttf')):
                            previous_glyph = fileList[file_index]["Font file"].getGlyphSet()[previous_glyphName]
                            xOffset = previous_glyph.width
                            
                            



                
                if file_path.endswith(".ufo"):
                    glyph = font[glyphName]
                    font_upm = font.info.unitsPerEm
                    
                    if pos == "left":
                        xOffset = -glyph.width
                    if pos == "right":
                        xOffset = xOffset
                        
                    translate(xOffset)

                    path = glyph.naked().getRepresentation("defconAppKit.NSBezierPath")
                    path.fill()

                if file_path.endswith(('.otf', '.ttf')):
                    font = TTFont(file_path)
                    glyph = font.getGlyphSet()[glyphName]

                    font_upm = font['head'].unitsPerEm
                    scaleValue = cf_upm / font_upm

                    if pos == "left":
                        xOffset = -glyph.width
                    if pos == "right":
                        xOffset = xOffset

                    translate(xOffset*scaleValue)

                    save()
                    path = self.draw_outline(glyph, font, scaleValue)
                    path.fill()
                    restore()
                    
        restore()


    def draw_outline(self, glyph, font, scaleValue):
        pen = CocoaPen(None)
        glyph.draw(pen)
        path = pen.path
        scale(scaleValue)
        return path


    def stringToGlyphs(self, text, path, font):
        glyphRecord = []

        if path.endswith(".ufo"):
            cmap = font.getCharacterMapping()
        if path.endswith(('.otf', '.ttf')):
            cmap = font.getBestCmap()
        
        if isinstance(text, str):
            text = text
        lines = text.split('\n')
        for line in lines:
            # Replace /? by current glyph name
            if "/?" in line:
                line = line.replace("/?", "/" + CurrentGlyph().name)
                
            glyphRecord += splitText(line, cmap)
            glyphRecord.append('\n')
        glyphRecord.pop()     
        return glyphRecord

    def dropCallback(self, sender, dropInfo):
        isProposal = dropInfo["isProposal"]
        existingPaths = sender.get()
        paths = dropInfo["data"]
        paths = [path for path in paths if path not in existingPaths]
        paths = [path for path in paths if os.path.splitext(path)[-1].lower() in self.supportedFontFileFormats or os.path.isdir(path)]
        if not paths:
            return False
        if not isProposal:
            for path in paths:
                glifFolder = f"{path}/glyphs"
                item = {}
                item['File name'] = path.split("/")[-1]
                item['File path'] = path
                if path.endswith('.ufo'):
                    item['Font file'] = OpenFont(path, showInterface=False)
                if path.endswith(('.otf', '.ttf')):
                    item['Font file'] = TTFont(path)
                
                self.font_order.append(item)
                self.w.fileList.append(item)
        return True


    def font_list_drop_callback(self, sender, dropInfo):
        
        for i in self.font_order:
            if i not in self.w.fileList.get():
                self.font_order.remove(i)
                
            
        isProposal = dropInfo["isProposal"]
        
        if not isProposal:
            # get the indexes
            from_index = int(dropInfo["data"][0])
            to_index = dropInfo["rowIndex"]
            
            if to_index != from_index:
                # get the selected object and remove it from the list
                item = self.font_order.pop(from_index)
                
                # fix indexes if the object is moved down the list
                if from_index < to_index:
                    to_index -= 1
                
                # Insert the item at the required index
                self.font_order.insert(to_index, item)
                # update the vanila list
                sender.set(self.font_order)

        UpdateCurrentGlyphView()
        return True

        
    def font_list_drag_callback(self, sender, index):
        return index

getListofFiles()
