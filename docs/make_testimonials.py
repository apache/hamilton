# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

card_template = """
        <div class="testimonial-card">
            <div class="testimonial-content">
                <p>"{user_quote}"</p>
                <h4>{user_name}</h4>
                <span>{user_title}, {user_company}</span>
            </div>
        </div>"""

testimonials = [
    {
        "user_name": "Yuan Liu",
        "user_title": "DS",
        "user_company": "Kora Financial",
        "user_quote": "Hamilton provides a modular and compatible framework that has significantly empowered our data science team. "
                      "We've been able to build robust and flexible data pipelines with ease. The documentation is thorough and regularly updated... "
                      "Even with no prior experience with the package, our team successfully migrated one of our legacy data pipelines to the Hamilton structure within a month. "
                      "This transition has greatly enhanced our productivity, enabling us to focus more on feature engineering and model iteration while Hamilton's DAG approach "
                      "seamlessly manages data lineage.<br/>I highly recommend Hamilton to data professionals looking for a reliable, standardized solution for creating and "
                      "managing data pipelines.",
        "image_link": "",
    },
    {
        "user_name": "Kyle Pounder",
        "user_title": "CTO",
        "user_company": "Wealth.com",
        "user_quote": "How (with good software practices) do you orchestrate a system of asynchronous LLM calls, but where some of them depend on others? "
                      "How do you build such a system so that it’s modular and testable? At wealth.com we've selected Hamilton to help us solve these problems "
                      "and others. And today our product, Ester AI, an AI legal assistant that extracts information from estate planning documents, is running "
                      "in production with Hamilton under the hood.",
        "image_link": "",
    },
    {
        "user_name": "Michał Siedlaczek",
        "user_title": "Senior DS/SWE",
        "user_company": "IBM",
        "user_quote": "Hamilton is simplicity. Its declarative approach to defining pipelines (as well as the UI to visualize them) makes testing and modifying "
                      "the code easy, and onboarding is quick and painless. Since using Hamilton, we have improved our efficiency of both developing new "
                      "functionality and onboarding new developers to work on the code. We deliver solutions more quickly than before.",
        "image_link": "",
    },
    {
        "user_name": "Fran Boon",
        "user_title": "Director",
        "user_company": "Oxehealth.com",
        "user_quote": "...The companion Hamilton UI has taken the value proposition up enormously with the ability to clearly show lineage & track execution times,"
                      " covering a major part of our observability needs",
        "image_link": "",
    },
    {
        "user_name": "Louwrens",
        "user_title": "Software Engineer",
        "user_company": "luoautomation.com",
        "user_quote": "Many thanks to writing such a great library. We are very excited about it and very pleased with so many decisions you've made. 🙏",
        "image_link": "",
    },
]

# code to generate testimonials
for testimonial in testimonials:
    print(card_template.format(**testimonial))
