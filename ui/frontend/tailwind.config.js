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

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./node_modules/react-tailwindcss-datepicker/dist/index.esm.js",
  ],
  theme: {
    fontFamily: {
      sans: ["Inter"],
      code: [
        "ui-monospace",
        "SFMono-Regular",
        "Menlo",
        "Monaco",
        "Consolas",
        "Liberation Mono",
        "Courier New",
        "monospace",
      ],
    },
    screens: {
      xs: "480px",
      sm: "640px",
      // => @media (min-width: 640px) { ... }

      md: "1024px",
      // => @media (min-width: 1024px) { ... }

      lg: "1280px",
      // => @media (min-width: 1280px) { ... }

      xl: "1600px",
      // => @media (min-width: 1600px) { ... }
    },
    extend: {
      width: {
        144: "36rem",
        192: "48rem",
      },
      height: {
        128: "32rem",
      },
      backgroundImage: {
        "hero-pattern": "url('/public/hero-background.svg')",
      },
      border: {
        10: "10px",
      },
      colors: {
        dwdarkblue: "rgb(43,49,82)",
        dwred: "rgb(234,85,86)",
        dwlightblue: "rgb(66,157,188)",
        dwwhite: "white",
        dwblack: "black",
        calltoaction: "slate-300",
      },
      visibility: ["group-hover"],
      fontSize: {
        "2xs": ["0.5rem", "0.66rem"],
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("tailwindcss-question-mark"),
    require("@tailwindcss/typography"),
    require("tailwind-scrollbar-hide"),
  ],
};
