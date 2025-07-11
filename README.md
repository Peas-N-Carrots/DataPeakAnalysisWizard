# Data Peak Analysis Wizard

This is a small project I created for a local biotech company. This company uses digital image correlation (DIC) software to measure the elongation of a material. Data about the elongation is saved as a .csv of the amount of elongation per sample location per frame. Previously, an employee would open the file in Excel and manually examine the rows of the spreadsheet to find the peaks in the data in order to make conclusions about the data (mean, median, middle, maximum of each peak). This was inefficient and non-standardized process, so I was enlisted to create a simple wizard application to streamline the company's data analysis.

The front end of the wizard was made using tkinter, and the back end processing and visualization was primarily done with Pandas and Matplotlib.

### Page 1
This is what the wizard will look like when you open it up
