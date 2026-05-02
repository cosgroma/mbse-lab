FROM node:16-alpine AS builder

ARG EXEC_VE_REPO=https://github.com/Open-MBEE/exec-ve.git
ARG EXEC_VE_REF=5.0.0
ARG VE_ENV=example
ENV VE_ENV=${VE_ENV}

WORKDIR /opt/mbee/ve

RUN apk add --no-cache git openssh
RUN git clone --depth 1 --branch "${EXEC_VE_REF}" "${EXEC_VE_REPO}" .
RUN git config --global url."https://".insteadOf git://
RUN yarn install
RUN yarn webpack --config webpack.config.ts --mode=production --bail

FROM nginx:mainline-alpine AS runtime

ENV NGINX_PORT=80
ENV VE_API_UPSTREAM=http://flexo-sysmlv2:8080

COPY --from=builder /opt/mbee/ve/dist /usr/share/nginx/html
COPY config/flexo-sysmlv2.json /usr/share/nginx/html/config/config.json
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
