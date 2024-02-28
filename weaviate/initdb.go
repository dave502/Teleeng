//go get github.com/weaviate/weaviate-go-client/v4

package main

import (
  "context"

  "github.com/weaviate/weaviate-go-client/v4/weaviate"
  "github.com/weaviate/weaviate-go-client/v4/weaviate/auth"
  "github.com/weaviate/weaviate/entities/models"
)

func main() {
  cfg := weaviate.Config{
    Host:   "some-endpoint.weaviate.network/",  // Replace with your endpoint
    Scheme: "https",
    AuthConfig: auth.ApiKey{Value: "YOUR-WEAVIATE-API-KEY"}, // Replace w/ your Weaviate instance API key
    Headers: map[string]string{
      "X-OpenAI-Api-Key": "YOUR-OPENAI-API-KEY",  // Replace with your inference API key
    },
  }

  client, err := weaviate.NewClient(cfg)
  if err != nil {
      panic(err)
  }

  classObj := &models.Class{
		Class:      "Question",
		Vectorizer: "text2vec-openai",  // If set to "none" you must always provide vectors yourself. Could be any other "text2vec-*" also.
		ModuleConfig: map[string]interface{}{
			"text2vec-openai": map[string]interface{}{},
			"generative-openai": map[string]interface{}{},
		},
	}

	// add the schema
	err = client.Schema().ClassCreator().WithClass(classObj).Do(context.Background())
	if err != nil {
	panic(err)
	}
}
