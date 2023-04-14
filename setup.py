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


"""Install, build and package the `colangflows` package."""

from setuptools import find_packages, setup

setup(
    name="colangflows",
    version="0.0.1",
    packages=find_packages(),
    author="NVIDIA",
    author_email="colangflows@nvidia.com",
    description="Colang Flows: Rails for Conversational AI.",
    long_description="Colang Flows is a framework for creating runtime rails for Conversational AI systems "
    "built using LLMs or other types of NLU/NLP pipelines.",
    long_description_content_type="text/markdown",
    url="",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: NVIDIA Proprietary",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={
        "console_scripts": ["colangflows=colangflows.__main__:app"],
    },
)
