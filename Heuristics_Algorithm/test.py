from heuristics_algorithm import Heuristics_Algorithm

main_dir = '../content/drive/MyDrive/s2/'
sg = Heuristics_Algorithm(budget=1000, qPairs = 100, delimiter='\t',  sourceFilePath=main_dir + 'sourceSample.tsv', targetFilePath=main_dir + 'targetSample.tsv')
sg.applyProcessing()
