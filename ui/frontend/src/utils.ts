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

import { IconType } from "react-icons";
import {
  AiOutlineCalendar,
  AiOutlineDatabase,
  AiOutlineFile,
  AiOutlineGroup,
  AiOutlineNumber,
  AiOutlineQuestion,
  AiOutlineStock,
} from "react-icons/ai";

import { GrConfigure } from "react-icons/gr";

import { BiBracket } from "react-icons/bi";
import { BsBraces, BsCardChecklist, BsFillXDiamondFill } from "react-icons/bs";
import { FaChartLine, FaFeather, FaPython } from "react-icons/fa";
// import { SiScikitlearn } from "react-icons/si";
import { RiParenthesesFill } from "react-icons/ri";
import { RxComponentBoolean } from "react-icons/rx";
import moment from "moment-timezone";

import { BsFiletypeCsv, BsFiletypeJson } from "react-icons/bs";
import { SiApachespark, SiScikitlearn } from "react-icons/si";
import {
  NodeMetadataPythonType1,
  NodeTemplate,
  RunStatusType,
} from "./state/api/friendlyApi";
import { TbLetterU } from "react-icons/tb";
import { VscQuote } from "react-icons/vsc";

// import * as moment from 'moment-timezone'

//TODO -- replace this all

export const parsePythonType = (pythonType: NodeMetadataPythonType1) => {
  return pythonType.type_name.replace("<class '", "").replace("'>", "");
};

export const getPythonTypeNameForDisplay = (
  pythonType: NodeMetadataPythonType1
) => {
  const parsed = parsePythonType(pythonType);
  const dotIndex = parsed.indexOf(".");
  if (dotIndex === -1) {
    return parsed;
  }
  return `${parsed.slice(dotIndex + 1)} (${parsed.slice(0, dotIndex)})`;
};

export const getAdapterIcon = (adapterType: string | undefined): IconType => {
  if (adapterType === "csv") {
    return BsFiletypeCsv;
  } else if (adapterType === "json") {
    return BsFiletypeJson;
  } else if (adapterType === "feather") {
    return FaFeather;
  } else if (adapterType === "pickle") {
    return FaPython;
  } else if (adapterType === "file") {
    return AiOutlineFile;
  } else if (adapterType === "parquet") {
    return BsFillXDiamondFill;
  } else {
    return AiOutlineDatabase;
  }
};
export const getPythonTypeIcon = (
  pythonType: NodeMetadataPythonType1 | undefined
): IconType => {
  if (!pythonType) {
    return AiOutlineQuestion;
  }
  let parsedTypeName = parsePythonType(pythonType);
  if (parsedTypeName.startsWith("typing.Annotated")) {
    parsedTypeName = parsedTypeName
      .replace("typing.Annotated[", "")
      .split(",")[0];
  }
  if (parsedTypeName === "pandas.core.series.Series") {
    return AiOutlineStock;
  } else if (parsedTypeName === "pandas.core.frame.DataFrame") {
    return AiOutlineDatabase;
  } else if (
    parsedTypeName === "pandas.core.groupby.generic.DataFrameGroupBy"
  ) {
    return AiOutlineGroup;
  } else if (parsedTypeName === "polars.series.series.Series") {
    return AiOutlineStock;
  } else if (parsedTypeName.startsWith("pandas.core.indexes")) {
    return AiOutlineStock;
  } else if (parsedTypeName === "polars.dataframe.frame.DataFrame") {
    return AiOutlineDatabase;
  } else if (parsedTypeName === "pyspark.sql.dataframe.DataFrame") {
    return AiOutlineDatabase;
  } else if (parsedTypeName === "pyspark.sql.session.SparkSession") {
    return SiApachespark;
  } else if (
    parsedTypeName.startsWith("numpy.float") ||
    parsedTypeName.startsWith("numpy.int")
  ) {
    return AiOutlineNumber;
  } else if (parsedTypeName === "hamilton.data_quality.base.ValidationResult") {
    return BsCardChecklist;
  } else if (parsedTypeName === "str") {
    return VscQuote;
  } else if (parsedTypeName.startsWith("numpy.ndarray")) {
    return FaChartLine;
  } else if (parsedTypeName === "int" || parsedTypeName === "float") {
    return AiOutlineNumber;
  } else if (parsedTypeName === "bool") {
    return RxComponentBoolean;
  } else if (parsedTypeName.toLowerCase().startsWith("tuple")) {
    return RiParenthesesFill;
  } else if (
    parsedTypeName.startsWith("list") ||
    parsedTypeName.startsWith("set") ||
    parsedTypeName.startsWith("typing.List")
  ) {
    return BiBracket;
  } else if (
    parsedTypeName.toLowerCase().startsWith("dict") ||
    parsedTypeName.startsWith("typing.Dict")
  ) {
    return BsBraces;
  } else if (parsedTypeName.startsWith("sklearn")) {
    return SiScikitlearn;
  } else if (parsedTypeName.startsWith("typing.Union")) {
    return TbLetterU;
  } else if (parsedTypeName.startsWith("datetime.date")) {
    return AiOutlineCalendar;
  } else if (parsedTypeName.startsWith("typing.Tuple")) {
    return RiParenthesesFill;
  } else if (parsedTypeName.toLowerCase().indexOf("config") >= 0) {
    return GrConfigure;
  } else {
    return AiOutlineQuestion;
  }
};
export const getPythonTypeIconFromNode = (node: NodeTemplate): IconType => {
  const isSource = extractTagFromNode(node, "hamilton.data_loader") === true;
  const isSink = extractTagFromNode(node, "hamilton.data_saver") === true;
  if (isSource || isSink) {
    const adapterType =
      extractTagFromNode(node, "hamilton.data_loader.source") ||
      extractTagFromNode(node, "hamilton.data_saver.sink");
    return getAdapterIcon(adapterType);
  }

  // TODO -- make this more generic
  const pythonType = node.output as NodeMetadataPythonType1;
  return getPythonTypeIcon(pythonType);
};

export function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(" ");
}

/**
 * Uniqifies then combines
 * Doesn't preserve order
 * @param l List of lists to combine
 */
export const uniqueCombine = <T>(...l: T[]) => {
  return Array.from(new Set(l.flatMap((_) => _)));
};

export const intersectArrays = <T>(l1: T[], l2: T[]) => {
  return l1.filter((x) => l2.includes(x));
};

/**
 * Displays time as a string
 * TODO -- use local timezone...
 * The timestamps coming from the server are not timezone specific
 * @param time
 * @returns
 */
export const parseTime = (time: string) => {
  return moment(time).utc().tz(moment.tz.guess()).format();
};

export const arraysOverlap = <T>(l1: T[], l2: T[]) => {
  return intersectArrays(l1, l2).length > 0;
};
//eslint-disable-next-line @typescript-eslint/no-explicit-any
export const extractTagFromNode = (node: NodeTemplate, tag: string): any => {
  if (!Object.prototype.hasOwnProperty.call(node.tags, tag)) {
    return undefined;
  }
  const key = tag as keyof typeof node.tags;
  return (node.tags || {})[key];
};

export const truncateAndRemoveTrailingZeroes = (
  num: number,
  digits: number
) => {
  // https://stackoverflow.com/questions/26299160/using-regex-how-do-i-remove-the-trailing-zeros-from-a-decimal-number
  return num
    .toFixed(digits)
    .replace(/^([\d,]+)$|^([\d,]+)\.0*$|^([\d,]+\.[0-9]*?)0*$/, "$1$2$3");
};

export const durationFormat = (
  startTime: string | undefined,
  endTime: string | undefined,
  currentTime: Date
) => {
  const startMillis = new Date(startTime || currentTime).getTime();
  const endMillis = new Date(endTime || currentTime).getTime();
  const durationMillis = endMillis - startMillis;
  // TODO -- display in a friendly way (E.G. 00:00:12.34, 00:01:12.56, etc...)
  // Calculate hours, minutes, seconds, and milliseconds
  let totalSeconds = durationMillis / 1000;
  const hours = Math.floor(totalSeconds / 3600);
  totalSeconds %= 3600;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  const milliseconds = Math.floor((durationMillis % 1000) / 10); // Reduce to two decimal places equivalent

  // Format the output
  const formattedHours = hours.toString().padStart(2, "0");
  const formattedMinutes = minutes.toString().padStart(2, "0");
  const formattedSeconds = seconds.toString().padStart(2, "0");
  const formattedMilliseconds = milliseconds.toString().padStart(2, "0");

  // Display the duration without days and including milliseconds
  return {
    formattedHours,
    formattedMinutes,
    formattedSeconds,
    formattedMilliseconds,
  };
};

const MAX_RUNTIME_SECONDS = 60 * 60 * 36; // 1.5 days

export const adjustStatusForDuration = (
  status: RunStatusType,
  startTime: string | undefined,
  endTime: string | undefined,
  currentTime: Date
) => {
  if (status !== "RUNNING") {
    return status;
  }
  const startMillis = new Date(startTime || currentTime).getTime();
  const endMillis = new Date(endTime || currentTime).getTime();
  const durationMillis = endMillis - startMillis;
  // TODO -- display in a friendly way (E.G. 00:00:12.34, 00:01:12.56, etc...)
  // Calculate hours, minutes, seconds, and milliseconds
  const totalSeconds = durationMillis / 1000;
  if (totalSeconds > MAX_RUNTIME_SECONDS) {
    return "TIMEOUT";
  }
  return status;
};
