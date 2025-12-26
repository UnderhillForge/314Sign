import express from 'express';
import { ApiResponse } from '../types/index.js';
import { dbHelpers } from '../database.js';

const router = express.Router();

// GET /api/rules - List all rules (database only)
router.get('/', async (req, res) => {
  try {
    const rules = dbHelpers.getAllRules();

    // Transform database results to API format
    const ruleItems = rules.map((rule: any) => ({
      id: rule.id,
      name: rule.name,
      days: JSON.parse(rule.days),
      startTime: rule.start_time,
      endTime: rule.end_time,
      menu: rule.menu_name,
      slideshow: rule.slideshow_path,
      enabled: rule.enabled === 1
    }));

    res.json({
      success: true,
      data: ruleItems
    } as ApiResponse<any[]>);
  } catch (error) {
    console.error('Error listing rules:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to list rules',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// GET /api/rules/:id - Get specific rule
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const ruleId = parseInt(id, 10);

    if (isNaN(ruleId)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid rule ID',
        message: 'Rule ID must be a number'
      } as ApiResponse);
    }

    const rule = dbHelpers.getRuleById(ruleId);

    if (!rule) {
      return res.status(404).json({
        success: false,
        error: 'Rule not found',
        message: `Rule with ID '${id}' does not exist`
      } as ApiResponse);
    }

    const ruleItem = {
      id: rule.id,
      name: rule.name,
      days: JSON.parse(rule.days),
      startTime: rule.start_time,
      endTime: rule.end_time,
      menu: rule.menu_name,
      slideshow: rule.slideshow_path,
      enabled: rule.enabled === 1
    };

    res.json({
      success: true,
      data: ruleItem
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error reading rule:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to read rule',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// POST /api/rules - Create new rule
router.post('/', async (req, res) => {
  try {
    const { name, days, startTime, endTime, menu, slideshow } = req.body;

    if (!name || typeof name !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Name is required and must be a string'
      } as ApiResponse);
    }

    if (!Array.isArray(days)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Days must be an array'
      } as ApiResponse);
    }

    // Create rule in database
    const result = dbHelpers.createRule(
      name,
      JSON.stringify(days),
      startTime || '00:00',
      endTime || '23:59',
      menu || undefined,
      slideshow || undefined
    );

    // Get the created rule ID
    const ruleId = result.lastInsertRowid;

    // Get the created rule
    const newRule = dbHelpers.getRuleById(ruleId);

    const ruleItem = {
      id: newRule.id,
      name: newRule.name,
      days: JSON.parse(newRule.days),
      startTime: newRule.start_time,
      endTime: newRule.end_time,
      menu: newRule.menu_name,
      slideshow: newRule.slideshow_path,
      enabled: newRule.enabled === 1
    };

    res.json({
      success: true,
      data: ruleItem,
      message: 'Rule created successfully'
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error creating rule:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create rule',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// PUT /api/rules/:id - Update rule
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const ruleId = parseInt(id, 10);
    const { name, days, startTime, endTime, menu, slideshow } = req.body;

    if (isNaN(ruleId)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid rule ID',
        message: 'Rule ID must be a number'
      } as ApiResponse);
    }

    if (!name || typeof name !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Name is required and must be a string'
      } as ApiResponse);
    }

    if (!Array.isArray(days)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request body',
        message: 'Days must be an array'
      } as ApiResponse);
    }

    // Update rule in database
    dbHelpers.updateRule(
      name,
      JSON.stringify(days),
      startTime || '00:00',
      endTime || '23:59',
      menu || undefined,
      slideshow || undefined,
      ruleId
    );

    // Get updated rule
    const updatedRule = dbHelpers.getRuleById(ruleId);

    const ruleItem = {
      id: updatedRule.id,
      name: updatedRule.name,
      days: JSON.parse(updatedRule.days),
      startTime: updatedRule.start_time,
      endTime: updatedRule.end_time,
      menu: updatedRule.menu_name,
      slideshow: updatedRule.slideshow_path,
      enabled: updatedRule.enabled === 1
    };

    res.json({
      success: true,
      data: ruleItem,
      message: 'Rule updated successfully'
    } as ApiResponse<any>);
  } catch (error) {
    console.error('Error updating rule:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update rule',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

// DELETE /api/rules/:id - Delete rule
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const ruleId = parseInt(id, 10);

    if (isNaN(ruleId)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid rule ID',
        message: 'Rule ID must be a number'
      } as ApiResponse);
    }

    // Delete rule from database
    dbHelpers.deleteRule(ruleId);

    res.json({
      success: true,
      message: `Rule deleted successfully`
    } as ApiResponse);
  } catch (error) {
    console.error('Error deleting rule:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to delete rule',
      message: error instanceof Error ? error.message : 'Unknown error'
    } as ApiResponse);
  }
});

export default router;
