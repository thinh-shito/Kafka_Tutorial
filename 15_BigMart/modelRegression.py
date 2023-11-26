import pyspark
import numpy as np
import random
from pyspark.sql import SparkSession
from pyspark.sql.functions import when, col, collect_set, mean
from pyspark.ml import Pipeline
from pyspark.ml.regression import LinearRegression
from pyspark.ml.linalg import Vectors
from pyspark.ml.feature import VectorAssembler, StringIndexer,VectorAssembler,OneHotEncoder,StandardScaler
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml import PipelineModel

class RegressionModel():
    
    def __init__(self,df = None,categoricalCols = [],continuousCols =[],labelCol = ''):
        self.df = df
        self.continuousCols = continuousCols
        self.categoricalCols = categoricalCols
        self.labelCol = labelCol

    def fitModel(self):
        indexers = StringIndexer(inputCols=self.categoricalCols, 
                                 outputCols=[f"{c}_indexed" for c in self.categoricalCols],
                                 handleInvalid="keep")

        # default setting: dropLast=True
        encoders = OneHotEncoder(inputCols = indexers.getOutputCols(),
                                 outputCols=[ f"{c}_encoded" for c in indexers.getOutputCols()])

        assembler = VectorAssembler(inputCols = encoders.getInputCols() + self.continuousCols , outputCol = "features")
        
        # normalizer = StandardScaler(inputCol = "features", outputCol="normalized_features")
        # normalizer_X = StandardScaler(inputCol = self.labelCol, outputCol="normalized_label")
    
        pipeline = Pipeline(stages = [indexers, encoders, assembler])

        self.model = pipeline.fit(self.df)

    def transform(self, df):

        data = df.withColumn('label',col(self.labelCol))
        data = self.model.transform(df)
        
        return data.select('features','label','prediction')
    def predict(self,df):
        data = self.model.transform(df)
        
        return data
    
    def loadPipeline(self, path):
        self.model = PipelineModel.load(path)
        
    def savePipline(self):
        self.model.save('REPROCESSING_PIPLINE/')
        
    def preprocess(self, df):
        data = df
        data = data.withColumn("Outlet_Size", 
                                     when(data.Outlet_Size.isNull(),
                                    	when(data.Outlet_Size.isin('Supermarket Type3',
                                    	                               'Supermarket Type2'),
                                    	    'Medium')\
                                    	.when(data.Outlet_Size == 'Grocery Store','Small')\
                                    	.when(data.Outlet_Location_Type == 'Tier 3','High')\
                                    	.when(data.Outlet_Location_Type == 'Tier 2','Small')\
                                    	.when(data.Outlet_Location_Type == 'Tier 1',
                                    	      random.choice(['Medium', 'Small']))\
										)\
										.otherwise(data.Outlet_Size))
        
        data = data.na.fill( float(12.857645339263398) ,['Item_Weight'])
        data = data.replace(to_replace ={'low fat':'Low Fat','LF':'Low Fat', 'reg':'Regular'}, subset = ['Item_Fat_Content'])
        return data
    
    def evaluate(prediction):
        evaluator = RegressionEvaluator(labelCol="label",
										predictionCol="prediction",
										metricName="rmse")
        rmse = evaluator.evaluate(prediction)
        print("Root Mean Squared Error (RMSE) on test data = %0.2f" % float(rmse))