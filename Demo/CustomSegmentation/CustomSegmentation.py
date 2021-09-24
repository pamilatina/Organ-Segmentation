import os
import unittest
import logging
import hashlib
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import SampleData
import numpy as np
from slicer.util import arrayFromVolume,updateTableFromArray,getNode,loadNodeFromFile, loadNodesFromFile
import vtkSegmentationCorePython as vtkSegmentationCore
import ScreenCapture

#
# CustomSegmentation
#

class CustomSegmentation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "CustomSegmentation"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#CustomSegmentation">module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

    # Additional initialization step after application startup is complete
    slicer.app.connect("startupCompleted()", registerSampleData)

#
# Register sample data sets in Sample Data module
#

def registerSampleData():
  """
  Add data sets to Sample Data module.
  """
  # It is always recommended to provide sample data for users to make it easy to try the module,
  # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

  import SampleData
  iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

  # To ensure that the source code repository remains small (can be downloaded and installed quickly)
  # it is recommended to store data sets that are larger than a few MB in a Github release.

  # CustomSegmentation1
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='CustomSegmentation',
    sampleName='CustomSegmentation1',
    # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
    # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
    thumbnailFileName=os.path.join(iconsPath, 'CustomSegmentation1.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
    fileNames='CustomSegmentation1.nrrd',
    # Checksum to ensure file integrity. Can be computed by this command:
    #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
    checksums = 'SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
    # This node name will be used when the data set is loaded
    nodeNames='CustomSegmentation1'
  )

  # CustomSegmentation2
  SampleData.SampleDataLogic.registerCustomSampleDataSource(
    # Category and sample name displayed in Sample Data module
    category='CustomSegmentation',
    sampleName='CustomSegmentation2',
    thumbnailFileName=os.path.join(iconsPath, 'CustomSegmentation2.png'),
    # Download URL and target file name
    uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
    fileNames='CustomSegmentation2.nrrd',
    checksums = 'SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
    # This node name will be used when the data set is loaded
    nodeNames='CustomSegmentation2'
  )

#
# CustomSegmentationWidget
#

class CustomSegmentationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/CustomSegmentation.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = CustomSegmentationLogic()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.imageThresholdSliderWidget.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.ui.invertOutputCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.invertedOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    
    #------------------------------------------------Mapping of User Interface to Functions----------------------------------------------- 
    # Buttons
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.ui.fetchButton.connect('clicked(bool)', self.onFetchButton)
    self.ui.histogramButton.connect('clicked(bool)', self.onHistogramButton)
    self.ui.fetch2Button.connect('clicked(bool)', self.onFetch2Button)
    self.ui.histogram2Button.connect('clicked(bool)', self.onHistogram2Button)
    self.ui.saveMrbButton.connect('clicked(bool)', self.onSaveScene('saved_mrb_scene.mrb'));
    self.ui.saveMrmlButton.connect('clicked(bool)', self.onSaveScene('saved_mrml_scene.mrml'));
    self.ui.savePngButton.connect('clicked(bool)',self.onSavePngButton);
    
    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference("InputVolume"):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors and sliders
    self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
    self.ui.invertedOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolumeInverse"))
    self.ui.imageThresholdSliderWidget.value = float(self._parameterNode.GetParameter("Threshold"))
    self.ui.invertOutputCheckBox.checked = (self._parameterNode.GetParameter("Invert") == "true")

    # Update buttons states and tooltips
    if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("OutputVolume"):
      self.ui.applyButton.toolTip = "Compute output volume"
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Select input and output volume nodes"
      self.ui.applyButton.enabled = False

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSelector.currentNodeID)
    self._parameterNode.SetParameter("Threshold", str(self.ui.imageThresholdSliderWidget.value))
    self._parameterNode.SetParameter("Invert", "true" if self.ui.invertOutputCheckBox.checked else "false")
    self._parameterNode.SetNodeReferenceID("OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

    self._parameterNode.EndModify(wasModified)
  
  def onFetchButton(self):
    """
    This method is called when the user Clicks on "Fetch data from GITHUB" button in the GUI.
    The method loads data from GITHUB release and displays it in viewports in 3D SLicer.
    """
    print('Fetch Button Pressed...............')
    
    #Clear the scene
    slicer.mrmlScene.Clear()
    
    #Generating Hash Values
    #filename= r"C:\Users\jaski\Downloads\3dSlicer\Segmentation.nrrd"
    #print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
    
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # CustomSegmentation3
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
    
    # Category and sample name displayed in Sample Data module
    category='CustomSegmentation',
    sampleName='CustomSegmentation3',
    thumbnailFileName=os.path.join(iconsPath, 'CustomSegmentation3.png'),
    
    uris="https://github.com/JassiGhuman/Segmentation/releases/download/SHA256/14b49c992e11d07d4e70873be53b45521be3ec0e857f83bec74a9c9598a77d8a",
    fileNames='CustomSegmentation3.nrrd',
    
    #Checksum to ensure file integrity. Can be computed by this command:
    checksums = 'SHA256:14b49c992e11d07d4e70873be53b45521be3ec0e857f83bec74a9c9598a77d8a',
    
    # This node name will be used when the data set is loaded
    nodeNames='CustomSegmentation3'
    )
    
    print('Start Loading data set')
    inputVolume = SampleData.downloadSample('CustomSegmentation3')
    print('Loaded data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    print('Fetch Completed')
    
    
  def onSaveScene(self,filename, properties={}):
    """
    This method is called when the user Clicks on "Save as .mrb" or "Save as .mrml" buttons in the GUI.
    This method saves the scene depending on the filename parameter.  
    """
    from slicer import app
    filetype = 'SceneFile'
    properties['fileName'] = filename
    return app.coreIOManager().saveNodes(filetype, properties)
  
  
  def onSavePngButton(self):
    """
    This method is called when the user Clicks on "Save as selected" button in the GUI.
    This method saves the scene depending on the option selected in the dropdown.
    """
    print("Inside onSavePngButton method");
    selectedOption = self.ui.pngComboBox.currentText
    print(selectedOption);
    if selectedOption == 'Capture 3D view as PNG with transparent background':
      renderWindow = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()
      renderWindow.SetAlphaBitPlanes(1)
      wti = vtk.vtkWindowToImageFilter()
      wti.SetInputBufferTypeToRGBA()
      wti.SetInput(renderWindow)
      writer = vtk.vtkPNGWriter()
      writer.SetFileName("saved3dview.png")
      writer.SetInputConnection(wti.GetOutputPort())
      writer.Write()
      print("3dsceneShot saved");
    elif selectedOption == "Capture all views as PNG":
      cap = ScreenCapture.ScreenCaptureLogic()
      cap.showViewControllers(False)
      cap.captureImageFromView(None, "allViewsShot.png")
      cap.showViewControllers(True)
      print("allViewsShot saved");
    elif selectedOption == "Capture full slicer Window":
      img = qt.QPixmap.grabWidget(slicer.util.mainWindow()).toImage()
      img.save("mainWindowShot.png")
      print("mainWindow saved");
    else:
      print("Select a valid Option");
  
  
  def onHistogramButton(self):
    """
    This method is called when the user clicks on 1st "Create Histogram" button in the GUI.
    This method generates histogram associated to "fetch data from GITHUB" button.  
    """
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')
    
    # Get a volume from SampleData and compute its histogram
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
    
    # Category and sample name displayed in Sample Data module
    category='CustomSegmentation',
    sampleName='CustomSegmentation3',
    thumbnailFileName=os.path.join(iconsPath, 'CustomSegmentation3.png'),
    uris="https://github.com/JassiGhuman/Segmentation/releases/download/SHA256/14b49c992e11d07d4e70873be53b45521be3ec0e857f83bec74a9c9598a77d8a",
    fileNames='CustomSegmentation3.nrrd',
    checksums = 'SHA256:14b49c992e11d07d4e70873be53b45521be3ec0e857f83bec74a9c9598a77d8a',
    # This node name will be used when the data set is loaded
    nodeNames='CustomSegmentation3'
    )
    inputVolume = SampleData.downloadSample('CustomSegmentation3')

    #volumeNode = SampleData.SampleDataLogic().downloadMRHead()
    histogram = np.histogram(arrayFromVolume(inputVolume), bins=50)

    chartNode = slicer.util.plot(histogram, xColumnIndex = 1)
    chartNode.SetYAxisRangeAuto(False)
    chartNode.SetYAxisRange(0, 4e5)
    
  def onHistogram2Button(self):
    """
    This method is called when the user clicks on 2nd "Create Histogram" button in the GUI.
    This method generates histogram associated to "fetch Brain Tumor Segmentation" button.  
    """
  
    #Clear the scene
    slicer.mrmlScene.Clear()
    
    # Load master volume
    sampleDataLogic = SampleData.SampleDataLogic()
    masterVolumeNode = sampleDataLogic.downloadMRBrainTumor1()

    # Create segmentation
    segmentationNode = slicer.vtkMRMLSegmentationNode()
    slicer.mrmlScene.AddNode(segmentationNode)
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)

    # Create seed segment inside tumor
    tumorSeed = vtk.vtkSphereSource()
    tumorSeed.SetCenter(-6, 30, 28)
    tumorSeed.SetRadius(10)
    tumorSeed.Update()
    segmentationNode.AddSegmentFromClosedSurfaceRepresentation(tumorSeed.GetOutput(), "Tumor", [1.0,0.0,0.0])

    # Create seed segment inside tumor 2
    referenceSeed = vtk.vtkSphereSource()
    referenceSeed.SetCenter(-6, -50, -10)
    referenceSeed.SetRadius(20)
    referenceSeed.Update()
    segmentationNode.AddSegmentFromClosedSurfaceRepresentation(referenceSeed.GetOutput(), "Reference", [0.0,0.0,1.0])

    # Create seed segment outside tumor
    backgroundSeedPositions = [[0,65,32], [1, -14, 30], [0, 28, -7], [0,30,64], [31, 33, 27], [-42, 30, 27]]
    append = vtk.vtkAppendPolyData()
    for backgroundSeedPosition in backgroundSeedPositions:
      backgroundSeed = vtk.vtkSphereSource()
      backgroundSeed.SetCenter(backgroundSeedPosition)
      backgroundSeed.SetRadius(10)
      backgroundSeed.Update()
      append.AddInputData(backgroundSeed.GetOutput())

    append.Update()
    backgroundSegmentId = segmentationNode.AddSegmentFromClosedSurfaceRepresentation(append.GetOutput(), "Background", [0.0,1.0,0.0])

    # Perform analysis
    ################################################

    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
    slicer.mrmlScene.AddNode(segmentEditorNode)
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)

    # Set up masking parameters
    segmentEditorWidget.setActiveEffectByName("Mask volume")
    effect = segmentEditorWidget.activeEffect()
    # set fill value to be outside the valid intensity range
    intensityRange = masterVolumeNode.GetImageData().GetScalarRange()
    effect.setParameter("FillValue", str(intensityRange[0]-1))
    # Blank out voxels that are outside the segment
    effect.setParameter("Operation", "FILL_OUTSIDE")
    # Create a volume that will store temporary masked volumes
    maskedVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "Temporary masked volume")
    effect.self().outputVolumeSelector.setCurrentNode(maskedVolume)

    # Create chart
    plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode", "Histogram")
    
    
    # Create histogram plot data series for each masked volume
    for segmentIndex in range(segmentationNode.GetSegmentation().GetNumberOfSegments()):
      # Set active segment
      segmentID = segmentationNode.GetSegmentation().GetNthSegmentID(segmentIndex)
      segmentEditorWidget.setCurrentSegmentID(segmentID)
      # Apply mask
      effect.self().onApply()
      # Compute histogram values
      histogram = np.histogram(arrayFromVolume(maskedVolume), bins=100, range=intensityRange)
      # Save results to a new table node
      segment = segmentationNode.GetSegmentation().GetNthSegment(segmentIndex)
      tableNode=slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", segment.GetName() + " histogram table")
      updateTableFromArray(tableNode, histogram)
      tableNode.GetTable().GetColumn(0).SetName("Count")
      tableNode.GetTable().GetColumn(1).SetName("Intensity")
      # Create new plot data series node
      plotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode", segment.GetName() + " histogram")
      plotSeriesNode.SetAndObserveTableNodeID(tableNode.GetID())
      plotSeriesNode.SetXColumnName("Intensity")
      plotSeriesNode.SetYColumnName("Count")
      plotSeriesNode.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeScatter)
      plotSeriesNode.SetMarkerStyle(slicer.vtkMRMLPlotSeriesNode.MarkerStyleNone)
      plotSeriesNode.SetUniqueColor()
      # Add plot to chart
      plotChartNode.AddAndObservePlotSeriesNodeID(plotSeriesNode.GetID())

    # Show chart in layout
    slicer.modules.plots.logic().ShowChartInLayout(plotChartNode)

    # Delete temporary node
    slicer.mrmlScene.RemoveNode(maskedVolume)
    slicer.mrmlScene.RemoveNode(segmentEditorNode)
    
    print('Histogram generated for Brain Tumor Segmentation')
  
  
  def onFetch2Button(self):
    """
    This method is called when the user clicks on "Fetch Brain tumor Segmentation" button in the GUI.
    This method displays segmented tumor in 3D object viewport.  
    """
    print('Fetching Brain tumor Segmentation Data ...............')
    
    #Clear the scene
    slicer.mrmlScene.Clear()
    
    # Load master volume
    sampleDataLogic = SampleData.SampleDataLogic()
    masterVolumeNode = sampleDataLogic.downloadMRBrainTumor1()

    # Create segmentation
    segmentationNode = slicer.vtkMRMLSegmentationNode()
    slicer.mrmlScene.AddNode(segmentationNode)
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)

    # Create seed segment inside tumor
    tumorSeed = vtk.vtkSphereSource()
    tumorSeed.SetCenter(-6, 30, 28)
    tumorSeed.SetRadius(10)
    tumorSeed.Update()
    segmentationNode.AddSegmentFromClosedSurfaceRepresentation(tumorSeed.GetOutput(), "Tumor", [1.0,0.0,0.0])

    # Create seed segment inside tumor 2
    referenceSeed = vtk.vtkSphereSource()
    referenceSeed.SetCenter(-6, -50, -10)
    referenceSeed.SetRadius(20)
    referenceSeed.Update()
    segmentationNode.AddSegmentFromClosedSurfaceRepresentation(referenceSeed.GetOutput(), "Reference", [0.0,0.0,1.0])

    # Create seed segment outside tumor
    backgroundSeedPositions = [[0,65,32], [1, -14, 30], [0, 28, -7], [0,30,64], [31, 33, 27], [-42, 30, 27]]
    append = vtk.vtkAppendPolyData()
    for backgroundSeedPosition in backgroundSeedPositions:
      backgroundSeed = vtk.vtkSphereSource()
      backgroundSeed.SetCenter(backgroundSeedPosition)
      backgroundSeed.SetRadius(10)
      backgroundSeed.Update()
      append.AddInputData(backgroundSeed.GetOutput())

    append.Update()
    backgroundSegmentId = segmentationNode.AddSegmentFromClosedSurfaceRepresentation(append.GetOutput(), "Background", [0.0,1.0,0.0])

    # Perform analysis
    ################################################

    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    # To show segment editor widget (useful for debugging): segmentEditorWidget.show()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
    slicer.mrmlScene.AddNode(segmentEditorNode)
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)

    # Set up masking parameters
    segmentEditorWidget.setActiveEffectByName("Mask volume")
    effect = segmentEditorWidget.activeEffect()
    # set fill value to be outside the valid intensity range
    intensityRange = masterVolumeNode.GetImageData().GetScalarRange()
    effect.setParameter("FillValue", str(intensityRange[0]-1))
    # Blank out voxels that are outside the segment
    effect.setParameter("Operation", "FILL_OUTSIDE")
    # Create a volume that will store temporary masked volumes
    maskedVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "Temporary masked volume")
    effect.self().outputVolumeSelector.setCurrentNode(maskedVolume)
    
    print('Brain tumor Segmentation Data Fetched Successfully...........')
   
    
  def onApplyButton(self):
    """
    Run processing when user clicks "Apply" button.
    """
    print('Apply Button Pressed...............')
    try:

      # Compute output
      self.logic.process(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(),
        self.ui.imageThresholdSliderWidget.value, self.ui.invertOutputCheckBox.checked)

      # Compute inverted output (if needed)
      if self.ui.invertedOutputSelector.currentNode():
        # If additional output volume is selected then result with inverted threshold is written there
        self.logic.process(self.ui.inputSelector.currentNode(), self.ui.invertedOutputSelector.currentNode(),
          self.ui.imageThresholdSliderWidget.value, not self.ui.invertOutputCheckBox.checked, showResult=False)

    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()


#
# CustomSegmentationLogic
#

class CustomSegmentationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("Threshold"):
      parameterNode.SetParameter("Threshold", "100.0")
    if not parameterNode.GetParameter("Invert"):
      parameterNode.SetParameter("Invert", "false")

  def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume or not outputVolume:
      raise ValueError("Input or output volume is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')

    # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
    cliParams = {
      'InputVolume': inputVolume.GetID(),
      'OutputVolume': outputVolume.GetID(),
      'ThresholdValue' : imageThreshold,
      'ThresholdType' : 'Above' if invert else 'Below'
      }
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    stopTime = time.time()
    logging.info('Processing completed in {0:.2f} seconds'.format(stopTime-startTime))

#
# CustomSegmentationTest
#

class CustomSegmentationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_CustomSegmentation1()

  def test_CustomSegmentation1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('CustomSegmentation1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = CustomSegmentationLogic()

    # Test algorithm with non-inverted threshold
    logic.process(inputVolume, outputVolume, threshold, True)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], threshold)

    # Test algorithm with inverted threshold
    logic.process(inputVolume, outputVolume, threshold, False)
    outputScalarRange = outputVolume.GetImageData().GetScalarRange()
    self.assertEqual(outputScalarRange[0], inputScalarRange[0])
    self.assertEqual(outputScalarRange[1], inputScalarRange[1])

    self.delayDisplay('Test passed')
