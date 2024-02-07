# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# # SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# # SPDX-License-Identifier: Apache-2.0
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# # http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# from nemoguardrails.embeddings.cache import KeyGenerator
# from nemoguardrails.embeddings.cache import MD5KeyGenerator
# from nemoguardrails.embeddings.cache import HashKeyGenerator
# from nemoguardrails.embeddings.cache import CacheStore
# from nemoguardrails.embeddings.cahce import RedisCacheStore
# from nemoguardrails.embeddings.cache import InMemoryCacheStore
# from nemoguardrails.embeddings.cache import FileSystemCacheStore

# from nemoguardrails.embeddings.basic import SentenceTransformerEmbeddingModel
# from nemoguardrails.embeddings.basic import FastEmbedEmbeddingModel
# from nemoguardrails.embeddings.basic import OpenAIEmbeddingModel


# ALL_OBJECTS = {
#     MD5KeyGenerator,
#     HashKeyGenerator,
#     FileSystemCacheStore,
#     RedisCacheStore,
#     InMemoryCacheStore,
#     SentenceTransformerEmbeddingModel,
#     FastEmbedEmbeddingModel,
#     OpenAIEmbeddingModel,
# }


# ALL_OBJECTS_DICT = {cls.__name__: cls for cls in ALL_OBJECTS}
# ALL_OBJECTS_DICT.update(
#     {to_snake_case(cls.__name__): cls for cls in ALL_OBJECTS}
# )


# def get(identifier):
#     """Retrieves an embedding or cache class instance.

#     The `identifier` may be the string name of a class.

#     >>> key_generator = embeddings.get("md5")
#     >>> type(key_genrator)
#     <class 'function'>
#     >>> metric = embeddings.get("CategoricalCrossentropy")
#     >>> type(metric)
#     <class '...metrics.CategoricalCrossentropy'>

#     You can also specify `config` of the metric to this function by passing dict
#     containing `class_name` and `config` as an identifier. Also note that the
#     `class_name` must map to a `Metric` class

#     >>> identifier = {"class_name": "CategoricalCrossentropy",
#     ...               "config": {"from_logits": True}}
#     >>> metric = metrics.get(identifier)
#     >>> type(metric)
#     <class '...metrics.CategoricalCrossentropy'>

#     Args:
#         identifier: A metric identifier. One of None or string name of a metric
#             function/class or metric configuration dictionary or a metric
#             function or a metric class instance

#     Returns:
#         A Keras metric as a `function`/ `Metric` class instance.
#     """
#     if identifier is None:
#         return None
#     if isinstance(identifier, dict):
#         obj = deserialize(identifier)
#     elif isinstance(identifier, str):
#         obj = ALL_OBJECTS_DICT.get(identifier, None)
#     else:
#         obj = identifier
#     if callable(obj):
#         if inspect.isclass(obj):
#             obj = obj()
#         return obj
#     else:
#         raise ValueError(f"Could not interpret metric identifier: {identifier}")
