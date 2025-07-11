# Data Peak Analysis Wizard

This is a small project I created for a local biotech company. This company uses digital image correlation (DIC) software to measure the elongation of a material. Data about the elongation is saved as a .csv of the amount of elongation per sample location per frame. Previously, an employee would open the file in Excel and manually examine the rows of the spreadsheet to find the peaks in the data in order to make conclusions about the data (mean, median, middle, maximum of each peak). This was inefficient and non-standardized process, so I was enlisted to create a simple wizard application to streamline the company's data analysis.

After developing this tool in close collaboration with the engineers who would be using it, the wizard was deployed to the company and is now used on a daily basis!

If you want to get your hands on this repo, you will need to install Python if you haven't already. Also, you will need to pip install matplotlib, pandas, and pyperclip. Tkinter, os, and abc I believe are included in Python by default.

Read how to use the wizard below.

### Page 1
![Page 1 screenshot](DICscreenshots/Page1.png)

This is what the wizard will look like when you first open it. Use this page to select a data file.
- Click "Browse" to choose a .csv file from your device.
- The entry box will populate with the file path which may be edited manually.
Once a valid file path is selected, the next button will become active.

### Page 2
![Page 2 screenshot](DICscreenshots/Page2.png)

Here, you will select individual or averaged groups of columns to analyze. The key shows the index of each column in the previously selected CSV.
- Use the key to input a range of indexes in the "Column(s) Range" entry box. Either...
 1. Manually specify columns using "," to separate individual indexes and ":" for ranges.
 2. Use the key to click, ctrl+click, and shift+click on the columns you want to include. The entry box will be auto-populated.
- Optionally input a "Group Name." If the box is left blank, the name will default to either the single column's heading from the CSV or "Avg" + the specified range of columns.
- Click "Add Data Column" when finished to confirm the group. Use the "Remove Last Added" and "Clear" buttons when you make a mistake.
Once at least one group has been confirmed, the next button will become active.

### Page 3
![Page 3 screenshot](DICscreenshots/Page3.png)

Adjust the parameters of the peak detection algorithm here.
- Each entry box has a default value that can be changed to adjust the specific thresholds and parameters used to detect peaks. Values that generate good results on one dataset may not generate good results on another.
- The "↻" button will refresh its adjacent field to its default value.
- The "?" button will give a short description about what the parameter does and how to leverage it.
As long as each box is populated, the "Visualize" button will be active. This opens a popup to review the results of the peak detection and must be viewed before moving on.

### Page 3 Popup
![Page 3 Popup screenshot](DICscreenshots/Page3Vis.png)

This page shows a graph of each group's data with highlighted regions to depict the ranges that were identified as peaks.
- The legend on top allows you to isolate single or specific groups' graphs instead of viewing them all on top of each other.
- Additionally, users may look at the legend to see how many peaks in each group are being detected.
- On this page, users should...
⋅⋅⋅⋅1. Ensure the correct number of peaks are being detected per group.
⋅⋅⋅⋅2. Ensure groups are each detecting the same number of peaks.
⋅⋅⋅⋅3. Verify that the detected peaks look accurate.
Once the user closes the popup, if the algorithm detected the same number of peaks per group, the next button will be activated. Any adjustments to parameters on Page 3 will require the user to double check the graph again before proceeding.

### Page 4
![Page 4 screenshot](DICscreenshots/Page4.png)

Customize what data will be generated and output regarding the detected peaks.
- Check on and off which data should be generated. For sine waves, maximum is probably the only relevant statistic; for the square wave pogos, middle or median are likely more important.
Once at least one box is checked, the next button will become active.

### Page 5
![Page 5 screenshot](DICscreenshots/Page5.png)

Finally, the last page lets you save the output data.
- Check the preview table to see the output data and make sure everything looks good. Each statistic has a column per group. Rows represent that group and statistic's value per peak.
- Click "Save" to select a destination location and save an output CSV.
- Click "Copy Table" to copy the contents of the table to your clipboard to paste into Excel.
Click "Finish" to close the wizard or "Restart" to quickly navigate back to page 1; this can be useful if you want to keep some settings for your next analysis (same groups and stats but different input file, same file but different groups, etc).
