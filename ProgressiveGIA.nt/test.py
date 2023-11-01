from progressivegiant import ProgressiveGIAnt



main_dir = '/home/njdaras/Downloads/data/'

alg = ProgressiveGIAnt(budget=1000, qPairs = 100, delimiter='\t',  sourceFilePath=main_dir + 'regions_gr.csv', targetFilePath=main_dir + 'wildlife_sanctuaries.csv', wScheme = 'MBR')
alg.applyProcessing()
