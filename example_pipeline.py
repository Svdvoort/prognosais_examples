from PrognosAIs import Pipeline

# Specify the configuration file
config_file = "config.yml"

# We create a pipeline based on this configuration file
pipeline = Pipeline.Pipeline(config_file)

# The pipeline will now run the pre-processing, training and evaluation.
pipeline.start_local_pipeline()
