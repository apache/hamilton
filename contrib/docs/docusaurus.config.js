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

// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

const organizationName = "dagworks-inc";
const projectName = "hamilton";  // fixed due to GitHub pages deployment

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Hamilton Dataflow Hub',
  tagline: 'Your place to find Hamilton dataflows',
  favicon: 'img/hamilton_logo_transparent_bkgrd.ico',

  // Set the production url of your site here
  url: `https://${organizationName}.github.io`,
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: `/`, // /${projectName}/`,

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: organizationName, // Usually your GitHub org/user name.
  projectName: projectName  , // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          // editUrl:
          //   'https://github.com/apache/contrib/hamilton/',
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          // editUrl:
          //   'https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
        gtag: {
          trackingID: 'G-TGB1H6EPP9',
        },
        sitemap: {
          changefreq: 'daily',
          priority: 0.5,
          // ignorePatterns: ['/tags/**'],
          filename: 'sitemap.xml',
        },
      }),
    ],
  ],

  scripts: ["/js/posthog.js"],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/hamilton-social-card.png',
      navbar: {
        title: 'Hamilton Dataflow Hub',
        logo: {
          alt: 'Hamilton',
          src: 'img/hamilton_logo.png',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'dataflowSidebar',
            position: 'left',
            label: 'Dataflows',
          },

          {to: '/blog', label: 'Changelog', position: 'left'},
          {
            type: 'search',
            position: 'left',
          },
          {to: '/leaderboard', label: 'Leaderboard', position: 'left'},
          {href: 'https://blog.dagworks.io', label: 'DAGWorks Blog', position: 'right'},
          {
            href: 'https://github.com/apache/hamilton',
            label: 'GitHub',
            position: 'right',
          },
            {
            href: 'https://www.tryhamilton.dev',
            label: 'Try Hamilton',
            position: 'right',
          },

        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Dataflows',
                to: '/docs/',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Twitter',
                href: 'https://twitter.com/hamilton_os',
              },
              {
                label: 'Slack',
                href: 'https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g',
              },
              // {
              //   label: 'Twitter',
              //   href: 'https://twitter.com/docusaurus',
              // },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Blog',
                to: '/blog',
              },
                {
                label: 'DAGWorks Blog',
                href: 'https://blog.dagworks.io',
              },
              {
                label: 'GitHub',
                href: 'https://github.com/apache/hamilton',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} DAGWorks, Inc. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
       algolia: {
      // The application ID provided by Algolia
      appId: '7TPE26LXI6',

      // Public API key: it is safe to commit it
      apiKey: '135438a0a051d2177e8cb40dca885ed6',

      indexName: 'hub-dagworks',

      // Optional: see doc section below
      contextualSearch: true,

      // Optional: Specify domains where the navigation should occur through window.location instead on history.push. Useful when our Algolia config crawls multiple documentation sites and we want to navigate with window.location.href to them.
      externalUrlRegex: 'external\\.com|domain\\.com',

      // Optional: Replace parts of the item URLs from Algolia. Useful when using the same search index for multiple deployments using a different baseUrl. You can use regexp or string in the `from` param. For example: localhost:3000 vs myCompany.com/docs
      // replaceSearchResultPathname: {
        //from: '/docs/', // or as RegExp: /\/docs\//
        //to: '/',
      // },

      // Optional: Algolia search parameters
      searchParameters: {},

      // Optional: path for search page that enabled by default (`false` to disable it)
      searchPagePath: 'search',

      //... other Algolia params
            insights: true,
    },
    }),
};

module.exports = config;
