/**
 * API 调用封装模块
 * 通过 window.API 暴露全局接口，供所有页面调用
 *
 * 使用示例:
 *   const machines = await API.machines.getAll();
 *   const id = await API.production.create({ machine_id: 1, ... });
 *   await API.production.update(id, { actual_quantity: 100 });
 *   await API.production.remove(id);
 */
;(function () {
  'use strict';

  var BASE = window.location.origin;

  // ----------------------------------------------------------------
  // 底层请求
  // ----------------------------------------------------------------

  /**
   * 通用 GET 请求
   * @param {string} path   - API 路径，如 '/api/machines'
   * @param {Object} params - 查询参数，如 { machine_id: 1, from: '2025-01-01' }
   * @returns {Promise<any>}
   */
  async function get(path, params) {
    params = params || {};
    var qs = buildQuery(params);
    var url = BASE + path + (qs ? '?' + qs : '');

    var res = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });

    return handleResponse(res);
  }

  /**
   * 通用 POST 请求
   * @param {string} path - API 路径
   * @param {Object} data - 请求体
   * @returns {Promise<any>}
   */
  async function post(path, data) {
    data = data || {};
    var url = BASE + path;

    var res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(data),
    });

    return handleResponse(res);
  }

  /**
   * 通用 PUT 请求
   * @param {string} path - API 路径
   * @param {Object} data - 请求体
   * @returns {Promise<any>}
   */
  async function put(path, data) {
    data = data || {};
    var url = BASE + path;

    var res = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(data),
    });

    return handleResponse(res);
  }

  /**
   * 通用 DELETE 请求
   * @param {string} path - API 路径
   * @returns {Promise<any>}
   */
  async function del(path) {
    var url = BASE + path;

    var res = await fetch(url, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' },
    });

    return handleResponse(res);
  }

  /**
   * 统一响应处理
   * @param {Response} res
   * @returns {Promise<any>}
   */
  async function handleResponse(res) {
    var json;
    try {
      json = await res.json();
    } catch (e) {
      throw new Error('服务器返回了非 JSON 响应 (HTTP ' + res.status + ')');
    }

    if (!res.ok) {
      var msg = json.error || ('请求失败 (HTTP ' + res.status + ')');
      throw new Error(msg);
    }

    return json;
  }

  /**
   * 将对象转为 query string
   * 自动跳过 null / undefined / 空字符串
   * @param {Object} params
   * @returns {string}
   */
  function buildQuery(params) {
    var parts = [];
    for (var key in params) {
      if (params.hasOwnProperty(key)) {
        var val = params[key];
        if (val !== null && val !== undefined && val !== '') {
          parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(val));
        }
      }
    }
    return parts.join('&');
  }

  // ----------------------------------------------------------------
  // 业务接口
  // ----------------------------------------------------------------

  var API = {

    /** 基础 URL（自动检测当前访问地址） */
    baseUrl: BASE,

    /** 底层方法，供特殊场景直接调用 */
    get: get,
    post: post,
    put: put,
    del: del,

    // ---- 机床 ----
    machines: {
      /** 获取所有机床列表 */
      getAll: function () {
        return get('/api/machines');
      },
      /** 根据 ID 获取单台机床 */
      getById: function (id) {
        return get('/api/machines/' + id);
      },
      /** 新增机床 */
      create: function (data) {
        return post('/api/machines', data);
      },
      /** 更新机床信息 */
      update: function (id, data) {
        return put('/api/machines/' + id, data);
      },
      /** 删除机床 */
      remove: function (id) {
        return del('/api/machines/' + id);
      },
    },

    // ---- 生产记录 ----
    production: {
      /** 新增生产记录 */
      create: function (data) {
        return post('/api/production', data);
      },
      /** 查询生产记录，params: { machine_id, from, to } */
      list: function (params) {
        return get('/api/production', params);
      },
      /** 根据 ID 获取单条生产记录 */
      getById: function (id) {
        return get('/api/production/' + id);
      },
      /** 更新生产记录 */
      update: function (id, data) {
        return put('/api/production/' + id, data);
      },
      /** 删除生产记录 */
      remove: function (id) {
        return del('/api/production/' + id);
      },
    },

    // ---- 保养记录 ----
    maintenance: {
      /** 新增保养记录 */
      create: function (data) {
        return post('/api/maintenance', data);
      },
      /** 查询保养记录，params: { machine_id } */
      list: function (params) {
        return get('/api/maintenance', params);
      },
      /** 根据 ID 获取单条保养记录 */
      getById: function (id) {
        return get('/api/maintenance/' + id);
      },
      /** 更新保养记录 */
      update: function (id, data) {
        return put('/api/maintenance/' + id, data);
      },
      /** 删除保养记录 */
      remove: function (id) {
        return del('/api/maintenance/' + id);
      },
    },

    // ---- 故障记录 ----
    faults: {
      /** 新增故障记录 */
      create: function (data) {
        return post('/api/faults', data);
      },
      /** 查询故障记录，params: { status } */
      list: function (params) {
        return get('/api/faults', params);
      },
      /** 根据 ID 获取单条故障记录 */
      getById: function (id) {
        return get('/api/faults/' + id);
      },
      /** 更新故障记录 */
      update: function (id, data) {
        return put('/api/faults/' + id, data);
      },
      /** 标记故障已解决 */
      resolve: function (id, resolution) {
        return post('/api/faults/' + id + '/resolve', { resolution: resolution });
      },
      /** 删除故障记录 */
      remove: function (id) {
        return del('/api/faults/' + id);
      },
    },

    // ---- 统计 ----
    stats: {
      /** 获取仪表盘概览统计数据 */
      overview: function () {
        return get('/api/stats');
      },
    },

    // ---- 点检模板 ----
    inspectionTemplates: {
      /** 获取某设备的点检模板 */
      getAll: function (machineId) {
        return get('/api/inspection-templates', { machine_id: machineId });
      },
      /** 新增点检模板项目 */
      create: function (data) {
        return post('/api/inspection-templates', data);
      },
      /** 更新点检模板项目 */
      update: function (id, data) {
        return put('/api/inspection-templates/' + id, data);
      },
      /** 删除点检模板项目 */
      remove: function (id) {
        return del('/api/inspection-templates/' + id);
      },
      /** 从其他设备复制模板 */
      copy: function (sourceMachineId, targetMachineId) {
        return post('/api/inspection-templates/copy', {
          source_machine_id: sourceMachineId,
          target_machine_id: targetMachineId,
        });
      },
    },

    // ---- 点检记录 ----
    inspection: {
      /** 提交点检记录 */
      create: function (data) {
        return post('/api/inspection', data);
      },
      /** 查询点检记录，params: { machine_id } */
      list: function (params) {
        return get('/api/inspection', params);
      },
      /** 根据 ID 获取单条点检记录 */
      getById: function (id) {
        return get('/api/inspection/' + id);
      },
      /** 删除点检记录 */
      remove: function (id) {
        return del('/api/inspection/' + id);
      },
    },
  };

  // ----------------------------------------------------------------
  // 暴露到全局
  // ----------------------------------------------------------------
  window.API = API;

})();
