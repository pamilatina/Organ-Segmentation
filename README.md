# Organ-Segmentation
Segmentation of human body organs and loading in VTK for visualization

Steps to configure code in your system.
1) Pull code from GITHUB Repo.
2) Open 3D Slicer. Click on Edit button from menubar and select "Application Settings".
3) Selct modules and add path of where CustomSegmentation.py file is present to additional modules paths. Sample Path: path(path of folder where you cloned the repo.) + Segmentation\CustomModules\Demo\CustomSegmentation
4) Click OK button and restart 3D Slicer.
5) Now extension is configured and you can access extension by clicking on Modules dropdown => Examples => Custom segmentation.

Tips for Fetching data:
1) After clicking "Fetch Data from GITHUB", click on "Add Data" and select segmentation.nrrd file from Repo and add it as segmentation(in dropdown) do not select Volume there.
2) Navigate to "Segment Editor" module and check if segment is selcted in segmentation dropdown.
3) Click on eye icon on segments which need to be viewed in 3D.
4) If 3D output is not visible in the viewport click on "show 3D" button.

Tip for Saving scenes:
All the files are saved by default in the folder where 3D slicer is installed. Sample Common path for Windows: C:\Users'username'\AppData\Local\NA-MIC\Slicer 4.11.20210226
