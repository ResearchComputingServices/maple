# Project Design

## Design Overview


### System Overview Diagram

![](fig/deployment_diagram.svg)

### Data structures

```mermaid
classDiagram

    class ModelIteration {
        +String type [bert, stm, lda]
        +Model level1model
        +Model level2model
        +Model level3model
        +Date createDate
        +Date modifyDate
        +String status [created, training, classifying, complete]
        +int article_count
        +[int] article_classified
    }
    class Model{
        +String uuid
        +String type [bert, stm, lda]
        +String name
        +int level
        +[Topic] topic
        -String path
    }
    class Topic{
        -String model_uuid
        +[String] keywords
        +String label
        +[String] dot_summary
        +Float prevalence
        +Point center
        ?+Object wordcloud
        ---plot over time, number of articles, sentiment around it.
    }
    class Proccessed {
        -String article_uuid
        -String ModelIteration
        -String model_type [bert, stm, lda]
        -String level_1_topic_uuid
        -Float level_1_prob
        -String level_2_topic_uuid
        -Float level_2_prob
        -String level_3_topic_uuid
        -Float level_3_prob
        -Point position
    }
    class ArticleEmbeddings {
        +String uuid
        +String shingle

    }
```


### Communication Protocol Table

### Sequence Diagrams


## GUI Design




