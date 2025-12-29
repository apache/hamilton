/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

// DateTimeDisplay.tsx
import React, { FC } from "react";
import dayjs from "dayjs";
import { durationFormat } from "../../utils";

interface DateTimeDisplayProps {
  datetime: string;
}

export const DateTimeDisplay: FC<DateTimeDisplayProps> = ({ datetime }) => {
  // Format the datetime prop using dayjs
  const formattedDate = dayjs(datetime).format("MMMM D, YYYY");
  const formattedTime = dayjs(datetime).format("h:mma");

  return (
    <div className="flex flex-row gap-2">
      <div className="bg-dwdarkblue/40 p-2 rounded-md shadow w-min">
        <span className="text-sm text-white">{formattedDate}</span>
      </div>
      <div className="bg-dwdarkblue/40 p-2 rounded-md shadow w-min hidden md:block">
        <span className="text-sm text-white">{formattedTime}</span>
      </div>
    </div>
  );
};

export const DurationDisplay = (props: {
  startTime: string | undefined;
  endTime: string | undefined;
  currentTime: Date;
}) => {
  const {
    formattedHours,
    formattedMinutes,
    formattedSeconds,
    formattedMilliseconds,
  } = durationFormat(
    props.startTime || undefined,
    props.endTime || undefined,
    new Date()
  );
  // const out = `${formattedHours}:${formattedMinutes}:${formattedSeconds}.${formattedMilliseconds}`;
  const getTextColor = (highlighted: boolean) => {
    if (!highlighted) {
      return "text-gray-300";
    }
    return ""; // default to standrd
  };
  const highlightHours = formattedHours !== "00";
  const highlightMinutes = formattedMinutes !== "00" || highlightHours;
  const highlightSeconds = true;
  const highlightMilliseconds = true;
  return (
    <div className="font-semibold flex gap-0">
      <span className={getTextColor(highlightHours)}>{formattedHours}</span>
      <span className={getTextColor(highlightHours && highlightMinutes)}>
        :
      </span>
      <span className={`${getTextColor(highlightMinutes)}`}>
        {formattedMinutes}
      </span>
      <span className={getTextColor(highlightMinutes && highlightSeconds)}>
        :
      </span>
      <span className={`${getTextColor(highlightSeconds)}`}>
        {formattedSeconds}
      </span>
      <span className={getTextColor(highlightSeconds && highlightMilliseconds)}>
        .
      </span>
      <span
        className={`${
          highlightMilliseconds
            ? getTextColor(highlightMilliseconds)
            : "text-gray-200"
        }`}
      >
        {formattedMilliseconds}
      </span>
    </div>
  );
};
