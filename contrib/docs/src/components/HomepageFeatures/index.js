// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Easy to Use',
    Svg: require('@site/static/img/undraw_hamilton_mountain.svg').default,
    description: (
      <>
        Hamilton was designed from the ground up to quickly and easily create
          dataflows. If you can draw a flow chart, you can create it in Hamilton.
          If you can read a python function you can understand a Hamilton dataflow.
      </>
    ),
  },
  {
    title: 'Focus on What Matters',
    Svg: require('@site/static/img/undraw_hamilton_tree.svg').default,
    description: (
      <>
        Hamilton allows you to easily focus on each step of your dataflow.
          Dataflows are also reusable and extensible so use this hub to help you
          find the code that you're looking for. Then if you need to make a change,
        you can <a href={"https://hamilton.apache.org/reference/dataflows/copy/#copy"}> copy </a>
        the dataflow and make your own version.
      </>
    ),
  },
  {
    title: 'Powered by Python',
    Svg: require('@site/static/img/undraw_hamilton_python.svg').default,
    description: (
      <>
        Hamilton is built by defining python functions. You can do anything you can
          do in python in a Hamilton dataflow, and run hamilton code
          anywhere python runs: in a notebook, in a script, with Ray, Dask, or Spark, or even
          in a web app.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
      <div>
          <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      <div className="row">
          </div>
      </div>
    </section>
      <section className={styles.features}>
    <div className={styles.videoWrapper}>
      <iframe
        src="https://www.loom.com/embed/ee3c984f51ba4d5baddab414df346f90?sid=4d5ee9d7-3be2-42b2-af29-793249d909ee"
        frameBorder="0"
        webkitallowfullscreen
        mozallowfullscreen
        allowFullScreen
      >
      </iframe>
    </div>
  </section>

          </div>
  );
}
